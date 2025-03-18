import os
import sys
import logging
import asyncio
import tempfile
import requests
import shutil
import aiohttp
from typing import List, Optional
import time

from services.tts.tts_base import TTSBase
from core.config import settings

logger = logging.getLogger(__name__)


class VietTTSProvider(TTSBase):
    def __init__(self, voice_model: str = "female"):
        logger.info(f"Khởi tạo VietTTSProvider với voice model: {voice_model}")
        # Chuyển đổi voice_model từ "female"/"male" sang "0"/"1" cho VietTTS CLI
        self._voice_id = "0" if voice_model == "female" else "1"
        # Lấy URL API từ biến môi trường hoặc sử dụng giá trị mặc định
        self.api_url = os.environ.get("VIETTTS_API_URL", "http://viet-tts:5000")
        logger.info(f"Sử dụng VietTTS API URL: {self.api_url} với voice ID: {self._voice_id}")

    async def synthesize(self, text: str, output_file: str) -> None:
        try:
            logger.info(f"Bắt đầu tổng hợp văn bản qua API: '{text[:50]}...'")

            # Đảm bảo thư mục đầu ra tồn tại
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            # Chuẩn bị dữ liệu cho request
            data = {
                "text": text,
                "voice": self._voice_id,
                "output_format": "wav",
                "return_url": False  # Yêu cầu trả về file trực tiếp
            }

            # Gọi API bất đồng bộ
            async with aiohttp.ClientSession() as session:
                try:
                    endpoint = f"{self.api_url}/synthesize"
                    logger.info(f"Gửi request đến {endpoint}")

                    # Thử kết nối với số lần thử lại
                    max_retries = 3
                    retry_delay = 2

                    for attempt in range(max_retries):
                        try:
                            async with session.post(endpoint, json=data, timeout=60) as response:
                                if response.status == 200:
                                    # Lưu trực tiếp nội dung của response vào file
                                    with open(output_file, 'wb') as f:
                                        f.write(await response.read())

                                    logger.info(f"Đã lưu tập tin âm thanh: {output_file}")
                                    break
                                else:
                                    error_text = await response.text()
                                    logger.error(f"API trả về lỗi (status {response.status}): {error_text}")

                                    if attempt < max_retries - 1:
                                        logger.info(
                                            f"Thử lại sau {retry_delay} giây (lần thử {attempt + 1}/{max_retries})")
                                        await asyncio.sleep(retry_delay)
                                        retry_delay *= 2  # Tăng thời gian chờ giữa các lần thử
                                    else:
                                        raise Exception(f"API trả về lỗi sau {max_retries} lần thử: {error_text}")
                        except aiohttp.ClientConnectionError as ce:
                            logger.warning(f"Lỗi kết nối: {str(ce)}")
                            if attempt < max_retries - 1:
                                logger.info(f"Thử lại sau {retry_delay} giây (lần thử {attempt + 1}/{max_retries})")
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2
                            else:
                                raise Exception(f"Không thể kết nối đến API sau {max_retries} lần thử: {str(ce)}")

                except Exception as api_error:
                    logger.exception(f"Lỗi gọi API: {str(api_error)}")
                    # Thử phương pháp thay thế - gọi API đồng bộ
                    self._synthesize_sync(text, output_file)

            # Kiểm tra file đầu ra
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info(f"Tổng hợp thành công: {output_file} ({os.path.getsize(output_file)} bytes)")
            else:
                raise Exception(f"File đầu ra không tồn tại hoặc rỗng: {output_file}")

        except Exception as e:
            logger.exception(f"Lỗi khi tổng hợp giọng nói với VietTTS: {str(e)}")
            raise

    def _synthesize_sync(self, text: str, output_file: str) -> None:
        """Phương thức dự phòng sử dụng requests đồng bộ nếu phương thức bất đồng bộ thất bại"""
        logger.info(f"Đang sử dụng phương thức đồng bộ để tổng hợp giọng nói")

        try:
            # Chuẩn bị dữ liệu cho request
            data = {
                "text": text,
                "voice": self._voice_id,
                "output_format": "wav",
                "return_url": False  # Nhận trực tiếp file audio
            }

            endpoint = f"{self.api_url}/synthesize"
            logger.info(f"Gửi request đồng bộ đến {endpoint}")

            # Gửi request với số lần thử lại
            max_retries = 3
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    response = requests.post(endpoint, json=data, timeout=60)

                    if response.status_code == 200:
                        # Lưu nội dung của response vào file
                        with open(output_file, 'wb') as f:
                            f.write(response.content)
                        logger.info(f"Đã lưu tập tin âm thanh (phương thức đồng bộ): {output_file}")
                        break
                    else:
                        logger.error(f"API trả về lỗi (status {response.status_code}): {response.text}")

                        if attempt < max_retries - 1:
                            logger.info(f"Thử lại sau {retry_delay} giây (lần thử {attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise Exception(f"API trả về lỗi sau {max_retries} lần thử: {response.text}")

                except requests.exceptions.RequestException as re:
                    logger.warning(f"Lỗi request: {str(re)}")
                    if attempt < max_retries - 1:
                        logger.info(f"Thử lại sau {retry_delay} giây (lần thử {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise Exception(f"Không thể gửi request đến API sau {max_retries} lần thử: {str(re)}")

        except Exception as e:
            logger.exception(f"Lỗi khi tổng hợp đồng bộ: {str(e)}")
            raise

    async def is_available(self) -> bool:
        try:
            logger.info(f"Kiểm tra trạng thái VietTTS API: {self.api_url}/health")

            async with aiohttp.ClientSession() as session:
                try:
                    max_retries = 3
                    retry_delay = 2

                    for attempt in range(max_retries):
                        try:
                            async with session.get(f"{self.api_url}/health", timeout=10) as response:
                                if response.status == 200:
                                    logger.info("VietTTS API có sẵn và hoạt động")
                                    return True
                                else:
                                    logger.warning(
                                        f"VietTTS API trả về mã trạng thái không thành công: {response.status}")

                                    if attempt < max_retries - 1:
                                        logger.info(
                                            f"Thử lại sau {retry_delay} giây (lần thử {attempt + 1}/{max_retries})")
                                        await asyncio.sleep(retry_delay)
                                        retry_delay *= 2
                                    else:
                                        return False
                        except aiohttp.ClientConnectionError:
                            logger.warning(f"Không thể kết nối đến VietTTS API (lần thử {attempt + 1}/{max_retries})")

                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2
                            else:
                                return False

                except Exception as e:
                    logger.exception(f"Lỗi kiểm tra VietTTS API: {str(e)}")
                    return False

        except Exception as e:
            logger.exception(f"Lỗi kiểm tra VietTTS API: {str(e)}")
            return False

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