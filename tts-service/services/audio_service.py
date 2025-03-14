import os
import asyncio
import logging
import tempfile
import time
import uuid
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status, BackgroundTasks
from bson import ObjectId

from core.config import settings
from db.repositories.audio_repository import AudioRepository
from db.repositories.text_repository import TextRepository
from models.audio import Audio, AudioSegment
from models.user import User
from schemas.audio import AudioCreate, TTSRequest
from services.tts.tts_factory import TTSFactory
from utils.firebase_firestore import upload_audio_to_firestore, upload_audio_segment_to_firestore, delete_audio_from_firestore
from utils.text_processor import preprocess_text, split_text_into_chunks, analyze_vietnamese_text
from utils.audio_utils import concatenate_audio_files, get_audio_duration

logger = logging.getLogger(__name__)


class AudioService:
    def __init__(self, audio_repository: AudioRepository, text_repository: TextRepository):
        self.audio_repository = audio_repository
        self.text_repository = text_repository
        self.tts_factory = TTSFactory()

    async def create_audio_request(self, request: TTSRequest, user: User) -> Audio:

        text = await self.text_repository.get_by_id(request.text_id)
        if not text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )

        if str(text.user_id) != str(user.id) and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        existing_audio = await self.audio_repository.get_by_text_id(request.text_id)
        if existing_audio and existing_audio.status == "completed":
            return existing_audio

        audio_data = {
            "text_id": ObjectId(request.text_id),
            "user_id": ObjectId(str(user.id)),
            "voice_model": request.voice_model,
            "format": request.format,
            "sample_rate": request.sample_rate,
            "url": "",
            "duration": 0.0,
            "segments": [],
            "status": "pending"
        }

        audio = await self.audio_repository.create(audio_data)
        return audio

    async def generate_audio(self, audio_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:

        audio = await self.audio_repository.get_by_id(audio_id)
        if not audio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio request not found"
            )

        await self.audio_repository.update_status(str(audio.id), "processing")

        background_tasks.add_task(self._process_audio_task, str(audio.id))

        return {"status": "processing", "message": "Audio generation started", "audio_id": str(audio.id)}

    async def get_audio(self, audio_id: str, user: User) -> Audio:
        """Lấy thông tin audio theo ID"""
        audio = await self.audio_repository.get_by_id(audio_id)

        if not audio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio not found"
            )

        if str(audio.user_id) != str(user.id) and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return audio

    async def get_user_audios(self, user: User, skip: int = 0, limit: int = 100) -> List[Audio]:
        """Lấy danh sách audio của người dùng"""
        return await self.audio_repository.get_by_user_id(str(user.id), skip, limit)

    async def delete_audio(self, audio_id: str, user: User) -> bool:
        """Xóa audio"""
        audio = await self.audio_repository.get_by_id(audio_id)

        if not audio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio not found"
            )

        # Kiểm tra quyền truy cập
        if str(audio.user_id) != str(user.id) and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        # Xóa file audio trên Firestore
        if audio.url and audio.url.startswith("firestore://"):
            try:
                await delete_audio_from_firestore(audio.url)
            except Exception as e:
                logger.warning(f"Error deleting audio file from Firestore: {str(e)}")

        # Xóa các segment file (nếu có)
        for segment in audio.segments:
            if segment.url and segment.url.startswith("firestore://"):
                try:
                    await delete_audio_from_firestore(segment.url)
                except Exception as e:
                    logger.warning(f"Error deleting segment file from Firestore: {str(e)}")

        return await self.audio_repository.delete(audio_id)

    async def _process_audio_task(self, audio_id: str) -> None:
        """Task nền xử lý tạo file audio"""
        try:
            # Lấy thông tin audio request
            audio = await self.audio_repository.get_by_id(audio_id)
            if not audio:
                logger.error(f"Audio request {audio_id} not found")
                return

            # Lấy nội dung văn bản
            text = await self.text_repository.get_by_id(str(audio.text_id))
            if not text:
                logger.error(f"Text {audio.text_id} not found")
                await self.audio_repository.update_status(audio_id, "failed", "Text not found")
                return

            # Cập nhật trạng thái của text
            await self.text_repository.update_status(str(text.id), "processing")

            # Tạo thư mục tạm thời để lưu trữ các file audio
            temp_dir = os.path.join(settings.TTS_TEMP_DIR, f"tts_{audio_id}_{uuid.uuid4().hex}")
            os.makedirs(temp_dir, exist_ok=True)

            try:
                # Tiền xử lý văn bản tiếng Việt
                processed_text = preprocess_text(text.content)

                # Phân tích văn bản để tách thành các đoạn tự nhiên
                chunks = analyze_vietnamese_text(processed_text)

                # Tạo TTS engine
                tts_engine = self.tts_factory.create_tts_engine(audio.voice_model)

                segments = []
                segment_files = []
                current_position = 0
                total_duration = 0.0

                # Xử lý từng đoạn văn bản
                for i, chunk in enumerate(chunks):
                    chunk_text = chunk["text"]
                    start_index = chunk["start_index"]
                    end_index = chunk["end_index"]

                    logger.info(
                        f"Processing segment {i + 1}/{len(chunks)}: [{start_index}:{end_index}] - '{chunk_text[:50]}...'")

                    # Đặt tên file cho segment
                    segment_filename = os.path.join(temp_dir, f"segment_{i}.wav")

                    # Tạo audio cho segment
                    await tts_engine.synthesize(chunk_text, segment_filename)

                    # Lấy thông tin về file audio vừa tạo
                    duration = get_audio_duration(segment_filename)

                    # Tạo URL tạm thời cho segment (sẽ được cập nhật sau)
                    segment_temp_url = f"temp_segment_{i}"

                    # Tạo thông tin segment
                    segment = {
                        "start_index": start_index,
                        "end_index": end_index,
                        "start_time": total_duration,
                        "end_time": total_duration + duration,
                        "text": chunk_text,
                        "url": segment_temp_url
                    }

                    segments.append(segment)
                    segment_files.append(segment_filename)
                    total_duration += duration

                    # Cập nhật trạng thái tiến độ
                    if (i + 1) % 5 == 0 or i == len(chunks) - 1:
                        progress_msg = f"Đã xử lý {i + 1}/{len(chunks)} đoạn văn bản"
                        await self.audio_repository.update_status(audio_id, f"processing ({i + 1}/{len(chunks)})")

                logger.info(f"Concatenating {len(segment_files)} audio segments...")
                # Ghép tất cả các segment thành một file audio hoàn chỉnh
                output_filename = os.path.join(temp_dir, f"output.{audio.format}")
                concatenate_audio_files(segment_files, output_filename)

                logger.info(f"Uploading audio file to Firestore...")
                # Upload file audio lên Firestore
                collection_path = "audios"
                firebase_url = await upload_audio_to_firestore(
                    output_filename,
                    collection_path,
                    f"{audio.user_id}_{audio.text_id}_{audio_id}"
                )

                # Upload từng segment (nếu cần)
                logger.info(f"Uploading {len(segments)} audio segments to Firestore...")
                for i, segment in enumerate(segments):
                    segment_id = f"segment_{i}"
                    segment_url = await upload_audio_segment_to_firestore(
                        segment_files[i],
                        collection_path,
                        f"{audio.user_id}_{audio.text_id}_{audio_id}",
                        segment_id
                    )
                    segments[i]["url"] = segment_url

                logger.info(f"Updating audio record in database...")
                # Cập nhật thông tin audio
                await self.audio_repository.update_with_segments(
                    audio_id,
                    firebase_url,
                    total_duration,
                    segments
                )

                # Cập nhật trạng thái của text
                await self.text_repository.update_status(str(text.id), "completed")

                logger.info(f"Audio generation completed successfully. Total duration: {total_duration:.2f} seconds")

            except Exception as e:
                logger.exception(f"Error while processing audio: {str(e)}")
                await self.audio_repository.update_status(audio_id, "failed", str(e))
                await self.text_repository.update_status(str(text.id), "failed", str(e))
                raise
            finally:
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass

        except Exception as e:
            logger.exception(f"Error in _process_audio_task: {str(e)}")
            try:
                await self.audio_repository.update_status(audio_id, "failed", str(e))
            except:
                pass