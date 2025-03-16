import logging
from typing import Dict, Type

from services.tts.F5TTS_provider import F5TTSProvider
from services.tts.tts_base import TTSBase
from services.tts.fallback_provider import FallbackTTSProvider

logger = logging.getLogger(__name__)


class TTSFactory:
    def __init__(self):
        self._engines: Dict[str, Type[TTSBase]] = {
            "f5-tts": F5TTSProvider,
            "fallback": FallbackTTSProvider,
        }
        self._instances: Dict[str, TTSBase] = {}

    def create_tts_engine(self, voice_model: str = None) -> TTSBase:
        if not voice_model:
            voice_model = "female"

        try:
            logger.info("Đang thử sử dụng F5-TTS engine")
            f5_engine = F5TTSProvider(voice_model)

            if f5_engine.is_available():
                logger.info("F5-TTS engine khả dụng")
                return f5_engine
            else:
                logger.warning("F5-TTS không khả dụng")
                raise ImportError("F5-TTS không khả dụng")

        except (ImportError, Exception) as f5_error:
            logger.warning(f"Không thể sử dụng F5-TTS: {str(f5_error)}")

            try:
                logger.info("Sử dụng fallback TTS engine")
                fallback_engine = FallbackTTSProvider(voice_model)
                return fallback_engine
            except Exception as fallback_error:
                logger.error(f"Tất cả TTS engines đều thất bại: {str(fallback_error)}")
                raise RuntimeError("Không thể sử dụng bất kỳ TTS engine nào")

    def get_available_voices(self) -> Dict[str, list]:
        voices = {}

        for engine_name, engine_class in self._engines.items():
            try:
                temp_instance = engine_class()
                voices[engine_name] = temp_instance.supported_voices
            except Exception as e:
                logger.error(f"Lỗi lấy voices từ {engine_name}: {str(e)}")
                voices[engine_name] = []

        return voices