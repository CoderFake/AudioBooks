import logging
from typing import Dict, Type

from core.config import settings
from services.tts.tts_base import TTSBase
from services.tts.vietTTS_provider import VietTTSProvider

logger = logging.getLogger(__name__)


class TTSFactory:
    def __init__(self):
        self._engines: Dict[str, Type[TTSBase]] = {
            "vietTTS": VietTTSProvider,
        }
        self._instances: Dict[str, TTSBase] = {}

    def create_tts_engine(self, voice_model: str = None) -> TTSBase:
        """
        Tạo một TTS engine dựa trên model giọng đã chọn

        Args:
            voice_model (str, optional): Model giọng (female, male, etc.).Maej định là None.

        Returns:
            TTSBase: TTS engine
        """
        if not voice_model:
            voice_model = settings.DEFAULT_VOICE_MODEL
        if voice_model in self._instances:
            return self._instances[voice_model]

        engine_class = self._engines.get("vietTTS")

        if not engine_class:
            logger.error(f"No TTS engine available for voice model: {voice_model}")
            raise ValueError(f"No TTS engine available for voice model: {voice_model}")

        engine = engine_class(voice_model)
        self._instances[voice_model] = engine

        return engine

    def get_available_voices(self) -> Dict[str, list]:

        voices = {}

        for engine_name, engine_class in self._engines.items():
            try:
                temp_instance = engine_class()
                voices[engine_name] = temp_instance.supported_voices
            except Exception as e:
                logger.error(f"Error getting voices from {engine_name}: {str(e)}")
                voices[engine_name] = []

        return voices