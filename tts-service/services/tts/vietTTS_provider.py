import os
import logging
import asyncio
import tempfile
import subprocess
from typing import List, Optional

from services.tts.tts_base import TTSBase

logger = logging.getLogger(__name__)


class VietTTSProvider(TTSBase):
    def __init__(self, voice_model: str = "female"):
        self._voice_model = voice_model if voice_model in self.supported_voices else "female"
        self._check_vietTTS_installation()

    async def synthesize(self, text: str, output_file: str) -> None:

        try:
            logger.info(f"Synthesizing text with VietTTS using {self._voice_model} voice")

            with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', encoding='utf-8', delete=False) as f:
                text_file = f.name
                f.write(text)

            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            command = [
                "python", "-m", "vietTTS.synthesize",
                "--input", text_file,
                "--output", output_file,
                "--model", f"infore_{self._voice_model}"
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Error synthesizing speech: {error_msg}")
                raise Exception(f"VietTTS synthesis failed: {error_msg}")

            os.unlink(text_file)

            logger.info(f"Successfully synthesized text to {output_file}")

        except Exception as e:
            logger.exception(f"Error synthesizing speech with VietTTS: {str(e)}")
            raise

    async def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["python", "-m", "vietTTS.synthesize", "--help"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"VietTTS is not available: {str(e)}")
            return False

    def _check_vietTTS_installation(self) -> None:
        try:
            import importlib
            vietTTS_spec = importlib.util.find_spec("vietTTS")
            if vietTTS_spec is None:
                logger.warning("VietTTS is not installed")
                return False

            model_dir = os.path.expanduser("~/.config/vietTTS")
            female_model = os.path.join(model_dir, "infore_female", "config.json")
            male_model = os.path.join(model_dir, "infore_male", "config.json")
            lexicon = os.path.join(model_dir, "lexicon.pkl")

            if not os.path.exists(female_model) and self._voice_model == "female":
                logger.warning(f"Female model not found at {female_model}")

            if not os.path.exists(male_model) and self._voice_model == "male":
                logger.warning(f"Male model not found at {male_model}")

            if not os.path.exists(lexicon):
                logger.warning(f"Lexicon file not found at {lexicon}")

            return True
        except Exception as e:
            logger.error(f"Error checking VietTTS installation: {str(e)}")
            return False

    @property
    def supported_voices(self) -> list:
        return ["female", "male"]

    @property
    def supported_formats(self) -> list:
        return ["wav", "mp3"]

    @property
    def name(self) -> str:
        return "VietTTS"