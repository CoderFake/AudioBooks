import os
import logging
import asyncio
import wave
import struct
import numpy as np

from services.tts.tts_base import TTSBase

logger = logging.getLogger(__name__)


class FallbackTTSProvider(TTSBase):

    def __init__(self, voice_model: str = "female"):
        logger.info(f"Initializing FallbackTTSProvider with voice model: {voice_model}")
        self._voice_model = voice_model if voice_model in self.supported_voices else "female"

    async def synthesize(self, text: str, output_file: str) -> None:
        try:
            logger.info(f"Generating fallback audio for text: '{text[:50]}...'")

            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            if self._voice_model == "female":
                frequency = 280
            else:
                frequency = 140

            duration = min(5.0, 0.1 * len(text))
            sample_rate = 24000
            amplitude = 16000

            samples = []
            num_samples = int(duration * sample_rate)
            for i in range(num_samples):
                sample = amplitude * np.sin(2 * np.pi * frequency * i / sample_rate)
                samples.append(int(sample))

            with wave.open(output_file, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                for sample in samples:
                    wav_file.writeframes(struct.pack('h', sample))

            logger.info(f"Successfully generated fallback audio: {output_file}")

        except Exception as e:
            logger.exception(f"Error generating fallback audio: {str(e)}")
            raise

    def is_available(self) -> bool:
        return True

    @property
    def supported_voices(self) -> list:
        return ["female", "male"]

    @property
    def supported_formats(self) -> list:
        return ["wav", "mp3"]

    @property
    def name(self) -> str:
        return "FallbackTTS"