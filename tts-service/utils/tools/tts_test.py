import os
import sys
import argparse
import tempfile
import importlib.util
import asyncio
import logging
from datetime import datetime

sys.path.insert(0, '/app')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("tts-test")

SAMPLE_TEXT = """
Xin chào! Đây là bài kiểm tra hệ thống chuyển đổi văn bản thành giọng nói.
Tiếng Việt có nhiều dấu và âm thanh đặc biệt.
Hệ thống TTS cần phát âm chính xác các từ, cụm từ và câu tiếng Việt.
"""


async def test_f5tts(output_dir, voice_model="female"):
    logger.info("Testing F5-TTS...")

    # Kiểm tra module f5_tts
    spec = importlib.util.find_spec("f5_tts")
    if spec is None:
        logger.error("F5-TTS is not installed. Can't run test.")
        return False

    try:
        # Thêm đường dẫn vào PYTHONPATH
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        # Import provider
        from services.tts.F5TTS_provider import F5TTSProvider

        # Khởi tạo provider
        provider = F5TTSProvider(voice_model)

        # Kiểm tra khả dụng
        if not provider.is_available():
            logger.error("F5-TTS models are not properly installed.")
            return False

        # Tạo tên file output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"f5tts_test_{voice_model}_{timestamp}.wav")

        # Tổng hợp giọng nói
        logger.info(f"Synthesizing text with F5-TTS to {output_file}")
        await provider.synthesize(SAMPLE_TEXT, output_file)

        # Kiểm tra kết quả
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            logger.info(f"Audio file created successfully: {output_file} ({file_size} bytes)")
            return True
        else:
            logger.error(f"Audio file was not created: {output_file}")
            return False

    except Exception as e:
        logger.exception(f"Error testing F5-TTS: {str(e)}")
        return False


async def test_fallback_tts(output_dir, voice_model="female"):
    logger.info("Testing Fallback TTS...")

    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        # Import provider
        from services.tts.fallback_provider import FallbackTTSProvider

        # Khởi tạo provider
        provider = FallbackTTSProvider(voice_model)

        # Tạo tên file output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"fallback_test_{voice_model}_{timestamp}.wav")

        # Tổng hợp giọng nói
        logger.info(f"Generating audio with Fallback TTS to {output_file}")
        await provider.synthesize(SAMPLE_TEXT, output_file)

        # Kiểm tra kết quả
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            logger.info(f"Audio file created successfully: {output_file} ({file_size} bytes)")
            return True
        else:
            logger.error(f"Audio file was not created: {output_file}")
            return False

    except Exception as e:
        logger.exception(f"Error testing Fallback TTS: {str(e)}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test TTS engines")
    parser.add_argument("--output-dir", default="./test_output", help="Directory to save test audio files")
    parser.add_argument("--f5tts", action="store_true", help="Test F5-TTS")
    parser.add_argument("--fallback", action="store_true", help="Test Fallback TTS")
    parser.add_argument("--all", action="store_true", help="Test all engines")
    parser.add_argument("--voice", default="female", choices=["female", "male"], help="Voice model to use")

    args = parser.parse_args()

    # Tạo thư mục output nếu chưa tồn tại
    os.makedirs(args.output_dir, exist_ok=True)
    logger.info(f"Audio files will be saved to: {os.path.abspath(args.output_dir)}")

    # Nếu không có tham số nào được chỉ định, test tất cả
    if not (args.all or args.f5tts  or args.fallback):
        args.all = True

    results = {}

    # Test F5-TTS
    if args.all or args.f5tts:
        results['f5tts'] = await test_f5tts(args.output_dir, args.voice)

    if args.all or args.fallback:
        results['fallback'] = await test_fallback_tts(args.output_dir, args.voice)

    logger.info("\n=== TEST RESULTS ===")
    for engine, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{engine}: {status}")

    if any(results.values()):
        logger.info("At least one TTS engine is working!")
    else:
        logger.error("All TTS engines failed!")


if __name__ == "__main__":
    asyncio.run(main())