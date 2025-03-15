import os
import sys
import logging
import asyncio

f5tts_src = '/opt/F5-TTS/src'
if f5tts_src not in sys.path:
    sys.path.append(f5tts_src)

from services.tts.tts_base import TTSBase

logger = logging.getLogger(__name__)


class F5TTSProvider(TTSBase):
    def __init__(self, voice_model: str = "female"):
        logger.info(f"Initializing F5TTSProvider with voice model: {voice_model}")
        self._voice_model = voice_model if voice_model in self.supported_voices else "female"

        # Đường dẫn đến model (Vocos)
        self._model_path = f"/opt/models/{self._voice_model}"

        logger.info(f"F5-TTS model path: {self._model_path}")

        # Kiểm tra config.json tồn tại
        config_path = os.path.join(self._model_path, "config.json")
        if not os.path.exists(config_path):
            logger.error(f"File config.json không tồn tại: {config_path}")
            raise FileNotFoundError(f"File config.json không tồn tại: {config_path}")

        logger.info(f"Config file tồn tại: {config_path}")

    async def synthesize(self, text: str, output_file: str) -> None:
        try:
            # Import f5_tts trong hàm để tránh lỗi import khi khởi tạo
            import f5_tts

            logger.info(f"Tạo âm thanh cho text: '{text[:50]}...'")
            logger.info(f"Model: {self._model_path}")
            logger.info(f"Output file: {output_file}")

            # Tạo thư mục output nếu chưa tồn tại
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            # Chạy trong executor để không block event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: f5_tts.synthesize(
                    text,
                    output_file,
                    model=self._model_path,
                    sample_rate=24000,
                    speed=1.0
                )
            )

            # Kiểm tra file đã được tạo chưa
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                logger.info(f"Đã tạo file audio thành công: {output_file} ({file_size} bytes)")
            else:
                logger.error(f"Không thể tạo file audio: {output_file}")
                raise FileNotFoundError(f"File audio không được tạo: {output_file}")

        except Exception as e:
            logger.exception(f"Lỗi khi tạo âm thanh với F5-TTS: {str(e)}")
            raise

    def is_available(self) -> bool:
        try:
            # Kiểm tra module f5_tts
            import f5_tts
            logger.info(f"F5-TTS có thể import: {f5_tts.__file__}")

            # Kiểm tra model
            if not os.path.exists(self._model_path):
                logger.warning(f"Model không tồn tại: {self._model_path}")
                return False

            config_path = os.path.join(self._model_path, "config.json")
            if not os.path.exists(config_path):
                logger.warning(f"File config.json không tồn tại: {config_path}")
                return False

            logger.info(f"F5-TTS khả dụng với model {self._voice_model}")
            return True
        except ImportError as e:
            logger.warning(f"F5-TTS không được cài đặt: {e}")
            return False
        except Exception as e:
            logger.warning(f"Lỗi kiểm tra F5-TTS: {str(e)}")
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