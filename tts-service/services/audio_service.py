import os
import asyncio
import logging
import tempfile
import time
import wave
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
from utils.firebase_storage import upload_file_to_firebase, delete_file_from_firebase
from utils.text_processor import preprocess_text, split_text_into_chunks, analyze_vietnamese_text
from utils.audio_utils import concatenate_audio_files, get_audio_duration

logger = logging.getLogger(__name__)


class AudioService:
    def __init__(self, audio_repository: AudioRepository, text_repository: TextRepository):
        self.audio_repository = audio_repository
        self.text_repository = text_repository
        self.tts_factory = TTSFactory()

    async def create_audio_request(self, request: TTSRequest, user: User) -> Audio:
        """Tạo yêu cầu chuyển văn bản thành giọng nói"""
        # Kiểm tra văn bản tồn tại
        text = await self.text_repository.get_by_id(request.text_id)
        if not text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )

        # Kiểm tra quyền truy cập (chỉ người tạo văn bản hoặc admin mới có quyền)
        if str(text.user_id) != str(user.id) and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        # Kiểm tra xem đã có audio cho văn bản này chưa
        existing_audio = await self.audio_repository.get_by_text_id(request.text_id)
        if existing_audio and existing_audio.status == "completed":
            # Nếu đã có và đã hoàn thành, trả về audio hiện có
            return existing_audio

        # Tạo yêu cầu audio mới
        audio_data = {
            "text_id": ObjectId(request.text_id),
            "user_id": ObjectId(str(user.id)),
            "voice_model": request.voice_model,
            "format": request.format,
            "sample_rate": request.sample_rate,
            "url": "",  # Sẽ được cập nhật sau khi tạo file audio
            "duration": 0.0,  # Sẽ được cập nhật sau khi tạo file audio
            "segments": [],  # Sẽ được cập nhật sau khi tạo file audio
            "status": "pending"
        }

        audio = await self.audio_repository.create(audio_data)
        return audio

    async def generate_audio(self, audio_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """Khởi động quá trình tạo audio nền (background task)"""
        audio = await self.audio_repository.get_by_id(audio_id)
        if not audio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio request not found"
            )

        # Cập nhật trạng thái
        await self.audio_repository.update_status(str(audio.id), "processing")

        # Khởi chạy task nền
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

        # Kiểm tra quyền truy cập
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

        # Xóa file audio trên Firebase Storage
        if audio.url:
            try:
                await delete_file_from_firebase(audio.url)
            except Exception as e:
                logger.warning(f"Error deleting audio file from Firebase: {str(e)}")

        # Xóa các segment file (nếu có)
        for segment in audio.segments:
            if segment.url:
                try:
                    await delete_file_from_firebase(segment.url)
                except Exception as e:
                    logger.warning(f"Error deleting segment file from Firebase: {str(e)}")

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

                logger.info(f"Uploading audio file to Firebase Storage...")
                # Upload file audio lên Firebase Storage
                firebase_filename = f"audios/{audio.user_id}/{audio.text_id}/{audio_id}.{audio.format}"
                firebase_url = await upload_file_to_firebase(output_filename, firebase_filename)

                # Upload từng segment (nếu cần)
                logger.info(f"Uploading {len(segments)} audio segments to Firebase Storage...")
                for i, segment in enumerate(segments):
                    segment_firebase_filename = f"audios/{audio.user_id}/{audio.text_id}/{audio_id}_segment_{i}.{audio.format}"
                    segment_url = await upload_file_to_firebase(segment_files[i], segment_firebase_filename)
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
                # Xóa thư mục tạm thời
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