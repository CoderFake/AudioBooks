import os
import logging
import asyncio
from typing import List, Optional

from services.tts.tts_base import TTSBase

logger = logging.getLogger(__name__)


class F5TTSProvider(TTSBase):
    def __init__(self, voice_model: str = "female"):
        logger.info(f"Initializing F5-TTS with voice model: {voice_model}")

        self._check_f5tts_installation()

        self._voice_model = voice_model if voice_model in self.supported_voices else "female"

        self._model_path = os.path.expanduser(f"~/.config/f5-tts/models/{self._voice_model}")

    def _check_f5tts_installation(self):
        try:
            import f5_tts
            logger.info("F5-TTS is installed")
            return True
        except ImportError as e:
            logger.warning(f"F5-TTS is not installed: {e}")
            raise

    async def synthesize(self, text: str, output_file: str) -> None:
        try:
            import f5_tts

            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: f5_tts.synthesize(
                    text,
                    output_file,
                    model=self._model_path,
                    sample_rate=22050,
                    speed=1.0
                )
            )

            logger.info(f"Successfully converted text to speech: {output_file}")

        except Exception as e:
            logger.exception(f"Error converting text with F5-TTS: {str(e)}")
            raise

    def is_available(self) -> bool:
        try:
            import f5_tts

            model_path = os.path.expanduser(f"~/.config/f5-tts/models/{self._voice_model}")
            if not os.path.exists(model_path):
                logger.warning(f"Model not found at {model_path}")
                return False

            config_file = os.path.join(model_path, "config.json")
            if not os.path.exists(config_file):
                logger.warning(f"Config file not found at {config_file}")
                return False

            return True
        except ImportError:
            logger.warning("F5-TTS is not installed")
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