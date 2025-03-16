import os
import logging
import asyncio
import tempfile
import subprocess
from typing import List, Optional
import sys

# Thêm đường dẫn tới thư mục VietTTS từ Hugging Face
viet_tts_path = '/opt/viet-tts'
if viet_tts_path not in sys.path and os.path.exists(viet_tts_path):
    sys.path.append(viet_tts_path)

from services.tts.tts_base import TTSBase

logger = logging.getLogger(__name__)


class VietTTSProvider(TTSBase):
    def __init__(self, voice_model: str = "female"):
        logger.info(f"Initializing VietTTSProvider with voice model: {voice_model}")
        self._voice_model = voice_model if voice_model in self.supported_voices else "female"
        self._check_viettts_installation()

    async def synthesize(self, text: str, output_file: str) -> None:
        try:
            logger.info(f"Synthesizing text with VietTTS using {self._voice_model} voice")
            logger.info(f"Output file: {output_file}")

            # Tạo file text tạm thời
            with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', encoding='utf-8', delete=False) as f:
                text_file = f.name
                f.write(text)

            # Đảm bảo thư mục output tồn tại
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            # Sử dụng Python trực tiếp để chạy script từ Hugging Face
            synthesize_script = os.path.join(viet_tts_path, "synthesize.py")

            # Các tham số: text file, output file, model
            command = [
                "python", synthesize_script,
                "--input", text_file,
                "--output", output_file,
                "--voice", self._voice_model
            ]

            # Ghi log lệnh thực thi
            logger.info(f"Executing command: {' '.join(command)}")

            # Thực thi lệnh
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if stdout:
                logger.info(f"STDOUT: {stdout.decode()}")
            if stderr:
                logger.warning(f"STDERR: {stderr.decode()}")

            # Kiểm tra kết quả
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Error synthesizing speech: {error_msg}")
                raise Exception(f"VietTTS synthesis failed: {error_msg}")

            # Xóa file tạm
            os.unlink(text_file)

            logger.info(f"Successfully synthesized text to {output_file}")

        except Exception as e:
            logger.exception(f"Error in VietTTS synthesis: {str(e)}")
            # Kiểm tra sự tồn tại của các files và scripts
            if os.path.exists(viet_tts_path):
                logger.info(f"VietTTS directory exists: {viet_tts_path}")
                logger.info(f"Contents: {os.listdir(viet_tts_path)}")
            else:
                logger.error(f"VietTTS directory not found: {viet_tts_path}")

            # Kiểm tra thêm môi trường
            logger.info(f"Current directory: {os.getcwd()}")
            logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

            raise

    def is_available(self) -> bool:
        try:
            if not os.path.exists(viet_tts_path):
                logger.error(f"VietTTS directory not found at {viet_tts_path}")
                return False

            synthesize_script = os.path.join(viet_tts_path, "synthesize.py")
            if not os.path.exists(synthesize_script):
                logger.error(f"Synthesize script not found at {synthesize_script}")
                return False

            # Kiểm tra lệnh python trực tiếp
            logger.info(f"Checking if VietTTS script can be executed: {synthesize_script}")
            result = subprocess.run(
                ["python", synthesize_script, "--help"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

            if result.returncode != 0:
                logger.error(f"Error executing VietTTS script: {result.stderr.decode()}")
                return False

            logger.info("VietTTS is available and can be executed")
            return True
        except Exception as e:
            logger.error(f"Error checking VietTTS availability: {str(e)}")
            return False

    def _check_viettts_installation(self) -> bool:
        try:
            # Kiểm tra thư mục VietTTS
            if not os.path.exists(viet_tts_path):
                logger.warning(f"VietTTS directory not found at {viet_tts_path}")
                return False

            # Kiểm tra script synthesize.py
            synthesize_script = os.path.join(viet_tts_path, "synthesize.py")
            if not os.path.exists(synthesize_script):
                logger.warning(f"VietTTS synthesize script not found at {synthesize_script}")
                return False

            # Liệt kê files trong thư mục
            logger.info(f"VietTTS files: {os.listdir(viet_tts_path)}")

            # Kiểm tra thư mục models
            models_dir = os.path.expanduser("~/.config/vietTTS")
            logger.info(f"Checking models directory: {models_dir}")

            if os.path.exists(models_dir):
                logger.info(f"Models directory contents: {os.listdir(models_dir)}")
            else:
                logger.warning(f"Models directory not found: {models_dir}")
                return False

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