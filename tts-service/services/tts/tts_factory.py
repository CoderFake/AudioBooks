import logging
from typing import Dict, Type

from services.tts.vietTTS_provider import VietTTSProvider
from services.tts.tts_base import TTSBase
from services.tts.fallback_provider import FallbackTTSProvider

logger = logging.getLogger(__name__)


class TTSFactory:
    def __init__(self):
        self._engines: Dict[str, Type[TTSBase]] = {
            "viettts": VietTTSProvider,
            "fallback": FallbackTTSProvider,
        }
        self._instances: Dict[str, TTSBase] = {}

    def create_tts_engine(self, voice_model: str = None) -> TTSBase:
        if not voice_model:
            voice_model = "female"

        try:
            logger.info("Đang thử sử dụng VietTTS engine")
            viettts_engine = VietTTSProvider(voice_model)

            if viettts_engine.is_available():
                logger.info("VietTTS engine khả dụng")
                return viettts_engine
            else:
                logger.warning("VietTTS không khả dụng")
                raise ImportError("VietTTS không khả dụng")

        except (ImportError, Exception) as viettts_error:
            logger.warning(f"Không thể sử dụng VietTTS: {str(viettts_error)}")

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