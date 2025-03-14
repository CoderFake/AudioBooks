import os
import logging
import asyncio
from typing import List, Optional

from services.tts.tts_base import TTSBase

logger = logging.getLogger(__name__)


class F5TTSProvider(TTSBase):
    def __init__(self, voice_model: str = "female"):
        logger.info(f"Khởi tạo F5-TTS với mô hình giọng: {voice_model}")

        self._check_f5tts_installation()

        self._voice_model = voice_model if voice_model in self.supported_voices else "female"

        self._model_path = os.path.expanduser(f"~/.config/f5-tts/models/{self._voice_model}")

    def _check_f5tts_installation(self):
        try:
            import f5_tts
            logger.info("F5-TTS đã được cài đặt")
        except ImportError:
            logger.warning("F5-TTS chưa được cài đặt.")
            raise

    async def synthesize(self, text: str, output_file: str) -> None:
        try:
            import f5_tts

            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            f5_tts.synthesize(
                text,
                output_file,
                model=self._model_path,
                sample_rate=22050,
                speed=1.0
            )

            logger.info(f"Chuyển đổi văn bản thành công: {output_file}")

        except Exception as e:
            logger.exception(f"Lỗi khi chuyển đổi văn bản bằng F5-TTS: {str(e)}")
            raise

    async def is_available(self) -> bool:
        try:
            import f5_tts

            model_path = os.path.expanduser(f"~/.config/f5-tts/models/{self._voice_model}")
            if not os.path.exists(model_path):
                logger.warning(f"Không tìm thấy model tại {model_path}")
                return False

            return True
        except ImportError:
            logger.warning("F5-TTS không được cài đặt")
            return False

    @property
    def supported_voices(self) -> list:
        return ["female", "male"]

    @property
    def supported_formats(self) -> list:
        return ["wav", "mp3"]

    @property
    def name(self) -> str:
        return "F5-TTS"