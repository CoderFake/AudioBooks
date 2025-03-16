from typing import Any, List, Optional
import logging
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import base64
import io

from api.dependencies import get_current_active_user, get_audio_repository, get_text_repository
from db.repositories.audio_repository import AudioRepository
from db.repositories.text_repository import TextRepository
from models.user import User
from models.audio import Audio
from services.audio_service import AudioService
from schemas.audio import AudioResponse, TTSRequest
from utils.firebase_firestore import download_audio_from_firestore

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[AudioResponse])
async def read_audios(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_active_user),
        audio_repository: AudioRepository = Depends(get_audio_repository)
) -> Any:
    audio_service = AudioService(audio_repository, None)
    audios = await audio_service.get_user_audios(current_user, skip, limit)

    result = []
    for audio in audios:
        result.append(AudioResponse(
            id=str(audio.id),
            text_id=str(audio.text_id),
            user_id=str(audio.user_id),
            voice_model=audio.voice_model,
            url=audio.url,
            duration=audio.duration,
            format=audio.format,
            sample_rate=audio.sample_rate,
            segments=audio.segments,
            status=audio.status,
            error=audio.error,
            created_at=audio.created_at.isoformat(),
            updated_at=audio.updated_at.isoformat()
        ))

    return result


@router.post("/synthesize", response_model=AudioResponse)
async def synthesize_text(
        request: TTSRequest,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_active_user),
        audio_repository: AudioRepository = Depends(get_audio_repository),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:

    audio_service = AudioService(audio_repository, text_repository)

    audio = await audio_service.create_audio_request(request, current_user)

    if audio.status == "pending":
        background_tasks.add_task(audio_service.generate_audio, str(audio.id), background_tasks)

    # Chuyển đổi đối tượng segments sang dictionary để tránh lỗi model_type
    segments_data = []
    for segment in audio.segments:
        segments_data.append({
            "start_index": segment.start_index,
            "end_index": segment.end_index,
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "text": segment.text,
            "url": segment.url
        })

    return AudioResponse(
        id=str(audio.id),
        text_id=str(audio.text_id),
        user_id=str(audio.user_id),
        voice_model=audio.voice_model,
        url=audio.url,
        duration=audio.duration,
        format=audio.format,
        sample_rate=audio.sample_rate,
        segments=segments_data,
        status=audio.status,
        error=audio.error,
        created_at=audio.created_at.isoformat(),
        updated_at=audio.updated_at.isoformat()
    )


@router.get("/{audio_id}", response_model=AudioResponse)
async def read_audio(
        audio_id: str,
        current_user: User = Depends(get_current_active_user),
        audio_repository: AudioRepository = Depends(get_audio_repository),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:
    audio_service = AudioService(audio_repository, text_repository)
    audio = await audio_service.get_audio(audio_id, current_user)

    return AudioResponse(
        id=str(audio.id),
        text_id=str(audio.text_id),
        user_id=str(audio.user_id),
        voice_model=audio.voice_model,
        url=audio.url,
        duration=audio.duration,
        format=audio.format,
        sample_rate=audio.sample_rate,
        segments=audio.segments,
        status=audio.status,
        error=audio.error,
        created_at=audio.created_at.isoformat(),
        updated_at=audio.updated_at.isoformat()
    )


@router.delete("/{audio_id}")
async def delete_audio(
        audio_id: str,
        current_user: User = Depends(get_current_active_user),
        audio_repository: AudioRepository = Depends(get_audio_repository),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:
    audio_service = AudioService(audio_repository, text_repository)
    success = await audio_service.delete_audio(audio_id, current_user)

    if success:
        return JSONResponse(content={"message": "Audio deleted successfully"})

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error deleting audio"
    )


@router.get("/{audio_id}/status")
async def get_audio_status(
        audio_id: str,
        current_user: User = Depends(get_current_active_user),
        audio_repository: AudioRepository = Depends(get_audio_repository)
) -> Any:
    audio = await audio_repository.get_by_id(audio_id)

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found"
        )

    if str(audio.user_id) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return {
        "id": str(audio.id),
        "status": audio.status,
        "error": audio.error,
        "url": audio.url if audio.status == "completed" else None,
        "duration": audio.duration if audio.status == "completed" else None,
        "updated_at": audio.updated_at.isoformat()
    }

@router.post("/{audio_id}/regenerate")
async def regenerate_audio(
        audio_id: str,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_active_user),
        audio_repository: AudioRepository = Depends(get_audio_repository),
        text_repository: TextRepository = Depends(get_text_repository)
) -> Any:
    audio = await audio_repository.get_by_id(audio_id)

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found"
        )

    if str(audio.user_id) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    await audio_repository.update_status(audio_id, "pending")

    audio_service = AudioService(audio_repository, text_repository)
    background_tasks.add_task(audio_service.generate_audio, audio_id, background_tasks)

    return {"status": "processing", "message": "Audio regeneration started"}


@router.get("/{audio_id}/stream")
async def stream_audio(
        audio_id: str,
        current_user: User = Depends(get_current_active_user),
        audio_repository: AudioRepository = Depends(get_audio_repository)
) -> Any:
    logger.info(f"Streaming audio request for audio_id: {audio_id}")

    audio = await audio_repository.get_by_id(audio_id)

    if not audio:
        logger.error(f"Audio not found: {audio_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found"
        )

    if str(audio.user_id) != str(current_user.id) and not current_user.is_admin:
        logger.error(f"Permission denied for user {current_user.id} to access audio {audio_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if audio.status != "completed":
        logger.error(f"Audio {audio_id} not ready for streaming (status: {audio.status})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio not ready for streaming"
        )

    logger.info(f"Audio URL: {audio.url}")

    if not audio.url:
        logger.error(f"Audio URL not available for {audio_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio URL not available"
        )

    # Create a temp file for streaming
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio.format}") as temp_file:
        temp_path = temp_file.name

    logger.info(f"Temporary file created at: {temp_path}")

    try:
        # Handle different URL types
        if audio.url.startswith("firestore://"):
            logger.info(f"Downloading from Firestore: {audio.url}")
            success = await download_audio_from_firestore(audio.url, temp_path)
        elif audio.url.startswith("local://"):
            logger.info(f"Copying from local storage: {audio.url}")
            # For local files, just copy the file
            local_path = audio.url.replace("local://", "")
            if os.path.exists(local_path):
                with open(local_path, "rb") as src, open(temp_path, "wb") as dst:
                    dst.write(src.read())
                success = True
                logger.info(f"File successfully copied from {local_path} to {temp_path}")
            else:
                logger.error(f"Local file not found: {local_path}")
                success = False
        elif audio.url.startswith("file://"):
            logger.info(f"Copying from file: {audio.url}")
            # For file:// URLs, just copy the file
            file_path = audio.url.replace("file://", "")
            if os.path.exists(file_path):
                with open(file_path, "rb") as src, open(temp_path, "wb") as dst:
                    dst.write(src.read())
                success = True
                logger.info(f"File successfully copied from {file_path} to {temp_path}")
            else:
                logger.error(f"File not found: {file_path}")
                success = False
        else:
            logger.error(f"Unsupported audio URL format: {audio.url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio URL format: {audio.url}"
            )

        if not success:
            logger.error(f"Failed to download/copy audio from {audio.url}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download audio"
            )

        # Check if the temp file exists and has content
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            logger.error(f"Temp file is empty or doesn't exist: {temp_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audio file is empty or not available"
            )

        logger.info(f"Streaming file {temp_path} with size {os.path.getsize(temp_path)} bytes")

        def iterfile():
            try:
                with open(temp_path, "rb") as f:
                    while chunk := f.read(8192):
                        yield chunk
            except Exception as e:
                logger.error(f"Error reading file during streaming: {str(e)}")
            finally:
                try:
                    logger.info(f"Removing temp file: {temp_path}")
                    os.unlink(temp_path)
                except Exception as e:
                    logger.error(f"Error removing temp file: {str(e)}")

        content_type = f"audio/{audio.format}"
        logger.info(f"Returning StreamingResponse with content type: {content_type}")
        return StreamingResponse(iterfile(), media_type=content_type)

    except Exception as e:
        logger.exception(f"Error streaming audio: {str(e)}")
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming audio: {str(e)}"
        )


@router.get("/{audio_id}/segments/{segment_id}/stream")
async def stream_audio_segment(
        audio_id: str,
        segment_id: str,
        current_user: User = Depends(get_current_active_user),
        audio_repository: AudioRepository = Depends(get_audio_repository)
) -> Any:
    logger.info(f"Streaming segment request for audio_id: {audio_id}, segment_id: {segment_id}")

    audio = await audio_repository.get_by_id(audio_id)

    if not audio:
        logger.error(f"Audio not found: {audio_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found"
        )

    if str(audio.user_id) != str(current_user.id) and not current_user.is_admin:
        logger.error(f"Permission denied for user {current_user.id} to access audio {audio_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if audio.status != "completed":
        logger.error(f"Audio {audio_id} not ready for streaming (status: {audio.status})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio not ready for streaming"
        )

    segment_idx = int(segment_id.replace("segment_", ""))
    if segment_idx < 0 or segment_idx >= len(audio.segments):
        logger.error(f"Segment {segment_id} not found for audio {audio_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Segment {segment_id} not found"
        )

    segment = audio.segments[segment_idx]
    logger.info(f"Segment URL: {segment.url}")

    if not segment.url:
        logger.error(f"Segment URL not available for {audio_id}/{segment_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Segment URL not available"
        )

    # Create a temp file for streaming
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio.format}") as temp_file:
        temp_path = temp_file.name

    logger.info(f"Temporary file created at: {temp_path}")

    try:
        # Handle different URL types
        if segment.url.startswith("firestore://"):
            logger.info(f"Downloading from Firestore: {segment.url}")
            success = await download_audio_from_firestore(segment.url, temp_path)
        elif segment.url.startswith("local://"):
            logger.info(f"Copying from local storage: {segment.url}")
            # For local files, just copy the file
            local_path = segment.url.replace("local://", "")
            if os.path.exists(local_path):
                with open(local_path, "rb") as src, open(temp_path, "wb") as dst:
                    dst.write(src.read())
                success = True
                logger.info(f"File successfully copied from {local_path} to {temp_path}")
            else:
                logger.error(f"Local file not found: {local_path}")
                success = False
        elif segment.url.startswith("file://"):
            logger.info(f"Copying from file: {segment.url}")
            # For file:// URLs, just copy the file
            file_path = segment.url.replace("file://", "")
            if os.path.exists(file_path):
                with open(file_path, "rb") as src, open(temp_path, "wb") as dst:
                    dst.write(src.read())
                success = True
                logger.info(f"File successfully copied from {file_path} to {temp_path}")
            else:
                logger.error(f"File not found: {file_path}")
                success = False
        else:
            logger.error(f"Unsupported segment URL format: {segment.url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported segment URL format: {segment.url}"
            )

        if not success:
            logger.error(f"Failed to download/copy segment from {segment.url}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download segment"
            )

        # Check if the temp file exists and has content
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            logger.error(f"Temp file is empty or doesn't exist: {temp_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Segment file is empty or not available"
            )

        logger.info(f"Streaming file {temp_path} with size {os.path.getsize(temp_path)} bytes")

        def iterfile():
            try:
                with open(temp_path, "rb") as f:
                    while chunk := f.read(8192):
                        yield chunk
            except Exception as e:
                logger.error(f"Error reading file during streaming: {str(e)}")
            finally:
                try:
                    logger.info(f"Removing temp file: {temp_path}")
                    os.unlink(temp_path)
                except Exception as e:
                    logger.error(f"Error removing temp file: {str(e)}")

        content_type = f"audio/{audio.format}"
        logger.info(f"Returning StreamingResponse with content type: {content_type}")
        return StreamingResponse(iterfile(), media_type=content_type)

    except Exception as e:
        logger.exception(f"Error streaming segment: {str(e)}")
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming segment: {str(e)}"
        )