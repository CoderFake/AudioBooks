import os
import sys
import logging
import asyncio
import tempfile
from typing import List, Optional


viet_tts_path = '/opt/viet-tts'
if viet_tts_path not in sys.path:
    sys.path.append(viet_tts_path)

from services.tts.tts_base import TTSBase

logger = logging.getLogger(__name__)

class VietTTSProvider(TTSBase):
    def __init__(self, voice_model: str = "female"):
        logger.info(f"Khởi tạo VietTTSProvider với voice model: {voice_model}")
        self._voice_model = voice_model if voice_model in self.supported_voices else "female"

    async def synthesize(self, text: str, output_file: str) -> None:
        try:
            logger.info(f"Bắt đầu tổng hợp văn bản: '{text[:50]}...'")

            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            code = f"""
                import sys
                sys.path.append('{viet_tts_path}')
                from vietTTS.synthesizer import Synthesizer
                from vietTTS.hifigan.mel2wave import Mel2Wave
                import soundfile as sf
                
                try:
                    text = '''{text}'''
                    print(f"Tổng hợp văn bản: {{text[:50]}}...")
                    
                    # Tổng hợp
                    mels = Synthesizer().synthesize(text)
                    wav = Mel2Wave().infer(mels)
                    
                    # Lưu file
                    sf.write('{output_file}', wav, 22050)
                    print('Tổng hợp thành công!')
                except Exception as e:
                    print(f"Error: {{e}}")
                    sys.exit(1)
                """

            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.py', delete=False) as tmp:
                script_path = tmp.name
                tmp.write(code)

            logger.info(f"Thực thi script")
            process = await asyncio.create_subprocess_exec(
                "python", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if stdout:
                logger.info(f"Output: {stdout.decode()}")
            if stderr:
                logger.error(f"Error: {stderr.decode()}")

            if process.returncode != 0:
                raise Exception(f"VietTTS failed with error: {stderr.decode() if stderr else 'Unknown error'}")

            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info(f"Tổng hợp giọng nói thành công: {output_file}")
            else:
                raise Exception("Output file is empty or doesn't exist")

            try:
                os.unlink(script_path)
            except Exception as e:
                logger.warning(f"Không thể xóa file tạm: {str(e)}")

        except Exception as e:
            logger.exception(f"Lỗi khi tổng hợp giọng nói với VietTTS: {str(e)}")
            raise

    def is_available(self) -> bool:
        try:
            import vietTTS
            from vietTTS.synthesizer import Synthesizer
            from vietTTS.hifigan.mel2wave import Mel2Wave

            logger.info(f"VietTTS được cài đặt tại: {vietTTS.__file__}")
            return True
        except ImportError as e:
            logger.error(f"VietTTS không khả dụng - lỗi import: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Lỗi kiểm tra VietTTS: {str(e)}")
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
