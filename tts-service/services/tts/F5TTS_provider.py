import os
import sys
import logging
import asyncio
import tempfile
from concurrent.futures import ThreadPoolExecutor

f5tts_src = '/opt/F5-TTS/src'
if f5tts_src not in sys.path:
    sys.path.append(f5tts_src)

from services.tts.tts_base import TTSBase

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class F5TTSProvider(TTSBase):
    def __init__(self, voice_model: str = "female"):
        logger.info(f"Initializing F5TTSProvider with voice model: {voice_model}")
        self._voice_model = voice_model if voice_model in self.supported_voices else "female"
        self._model_path = f"/opt/models/{self._voice_model}"
        self._reference_audio = "/opt/F5-TTS/src/f5_tts/infer/examples/basic/basic_ref_en.wav"
        self._reference_text = "Some call me nature, others call me mother nature."

        # Không khởi tạo model trong __init__ để tránh chặn luồng
        self._tts_model = None

        # Kiểm tra config.json
        config_path = os.path.join(self._model_path, "config.json")
        if not os.path.exists(config_path):
            logger.error(f"File config.json không tồn tại: {config_path}")
            raise FileNotFoundError(f"File config.json không tồn tại: {config_path}")

    async def synthesize(self, text: str, output_file: str) -> None:
        """
        Chuyển đổi văn bản thành âm thanh sử dụng F5-TTS,
        chạy trong executor riêng để không chặn luồng chính
        """
        try:
            logger.info(f"Tạo âm thanh cho văn bản: '{text[:50]}...'")

            # Tạo thư mục output nếu chưa tồn tại
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            # Hàm tổng hợp sẽ chạy trong thread riêng
            def _run_synthesis():
                try:
                    # Import và khởi tạo model trong thread
                    from f5_tts.api import F5TTS
                    tts = F5TTS(model="F5TTS_v1_Base")

                    # Gọi phương thức infer
                    wav, sr, _ = tts.infer(
                        ref_file=self._reference_audio,
                        ref_text=self._reference_text,
                        gen_text=text,
                        file_wave=output_file,
                        remove_silence=True
                    )
                    return True
                except Exception as e:
                    logger.error(f"Lỗi tổng hợp âm thanh: {str(e)}")
                    return False

            # Chạy trong executor để không chặn event loop
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(_executor, _run_synthesis)

            # Kiểm tra kết quả
            if success and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                logger.info(f"Tạo âm thanh thành công: {output_file} ({file_size} bytes)")
            else:
                raise Exception(f"Không thể tạo file âm thanh: {output_file}")

        except Exception as e:
            logger.exception(f"Lỗi khi tạo âm thanh với F5-TTS: {str(e)}")
            raise

    def is_available(self) -> bool:
        """Kiểm tra xem F5-TTS có khả dụng không"""
        try:
            # Kiểm tra module
            import importlib.util
            f5tts_api_spec = importlib.util.find_spec("f5_tts.api")
            if f5tts_api_spec is None:
                logger.warning("Không tìm thấy module f5_tts.api")
                return False

            # Kiểm tra file tham chiếu
            if not os.path.exists(self._reference_audio):
                logger.warning(f"File âm thanh tham chiếu không tồn tại: {self._reference_audio}")
                return False

            # Kiểm tra model path
            if not os.path.exists(self._model_path):
                logger.warning(f"Thư mục model không tồn tại: {self._model_path}")
                return False

            # Kiểm tra config
            config_path = os.path.join(self._model_path, "config.json")
            if not os.path.exists(config_path):
                logger.warning(f"File config.json không tồn tại: {config_path}")
                return False

            # Thử import F5TTS
            from f5_tts.api import F5TTS
            logger.info("Module F5TTS đã được import thành công")

            return True

        except ImportError as e:
            logger.warning(f"Không thể import f5_tts.api: {str(e)}")
            return False
        except Exception as e:
            logger.warning(f"Lỗi khi kiểm tra F5-TTS: {str(e)}")
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