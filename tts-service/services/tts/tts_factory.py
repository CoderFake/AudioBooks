import logging
from typing import Dict, Type

from services.tts.F5TTS_provider import F5TTSProvider
from services.tts.tts_base import TTSBase
from services.tts.vietTTS_provider import VietTTSProvider

logger = logging.getLogger(__name__)


class TTSFactory:
    def __init__(self):
        self._engines: Dict[str, Type[TTSBase]] = {
            "f5-tts": F5TTSProvider,
            "vietTTS": VietTTSProvider,
        }
        self._instances: Dict[str, TTSBase] = {}

    def create_tts_engine(self, voice_model: str = None) -> TTSBase:
        if not voice_model:
            voice_model = "female"

        try:
            f5_engine = F5TTSProvider(voice_model)

            if f5_engine.is_available():
                logger.info("Sử dụng F5-TTS thành công")
                return f5_engine
            else:
                raise ImportError("F5-TTS không khả dụng")

        except (ImportError, Exception) as f5_error:
            logger.warning(f"Không thể sử dụng F5-TTS: {str(f5_error)}")

            try:
                viet_tts_engine = VietTTSProvider(voice_model)
                logger.info("Chuyển sang sử dụng VietTTS")
                return viet_tts_engine

            except Exception as viet_error:
                logger.error(f"Cả F5-TTS và VietTTS đều không thể sử dụng: {str(viet_error)}")
                raise RuntimeError("Không tìm thấy bất kỳ TTS engine nào để sử dụng")

    def get_available_voices(self) -> Dict[str, list]:
        voices = {}

        for engine_name, engine_class in self._engines.items():
            try:
                temp_instance = engine_class()
                voices[engine_name] = temp_instance.supported_voices
            except Exception as e:
                logger.error(f"Lỗi khi lấy giọng từ {engine_name}: {str(e)}")
                voices[engine_name] = []

        return voices