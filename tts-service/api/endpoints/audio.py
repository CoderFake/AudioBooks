from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import base64
import io
import tempfile
import os

from api.dependencies import get_current_active_user, get_audio_repository, get_text_repository
from db.repositories.audio_repository import AudioRepository
from db.repositories.text_repository import TextRepository
from models.user import User
from models.audio import Audio
from services.audio_service import AudioService
from schemas.audio import AudioResponse, TTSRequest
from utils.firebase_firestore import download_audio_from_firestore

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

    if audio.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio not ready for streaming"
        )

    if not audio.url or not audio.url.startswith("firestore://"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio not available in Firestore"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio.format}") as temp_file:
        temp_path = temp_file.name

    try:
        success = await download_audio_from_firestore(audio.url, temp_path)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download audio from Firestore"
            )

        def iterfile():
            with open(temp_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk

            try:
                os.unlink(temp_path)
            except:
                pass

        content_type = f"audio/{audio.format}"
        return StreamingResponse(iterfile(), media_type=content_type)

    except Exception as e:
        try:
            os.unlink(temp_path)
        except:
            pass

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

    if audio.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio not ready for streaming"
        )

    segment_idx = int(segment_id.replace("segment_", ""))
    if segment_idx < 0 or segment_idx >= len(audio.segments):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Segment {segment_id} not found"
        )

    segment = audio.segments[segment_idx]

    if not segment.url or not segment.url.startswith("firestore://"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Segment not available in Firestore"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio.format}") as temp_file:
        temp_path = temp_file.name

    try:
        success = await download_audio_from_firestore(segment.url, temp_path)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download segment from Firestore"
            )

        def iterfile():
            with open(temp_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk

            try:
                os.unlink(temp_path)
            except:
                pass

        content_type = f"audio/{audio.format}"
        return StreamingResponse(iterfile(), media_type=content_type)

    except Exception as e:
        try:
            os.unlink(temp_path)
        except:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming segment: {str(e)}"
        )