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


async def test_f5tts_api(output_dir, voice_model="female"):
    logger.info("Kiểm tra F5-TTS API...")

    try:
        from f5_tts.api import F5TTS

        # Tạo tên file output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"f5tts_api_test_{voice_model}_{timestamp}.wav")

        # Khởi tạo F5-TTS
        logger.info("Khởi tạo model F5-TTS...")
        tts = F5TTS(model="F5TTS_v1_Base")

        # Đường dẫn đến file âm thanh tham chiếu
        ref_file = "/opt/F5-TTS/src/f5_tts/infer/examples/basic/basic_ref_en.wav"
        ref_text = "Some call me nature, others call me mother nature."

        # Kiểm tra xem file có tồn tại không
        if not os.path.exists(ref_file):
            logger.error(f"File âm thanh tham chiếu không tồn tại: {ref_file}")
            return False

        # Tổng hợp giọng nói
        logger.info(f"Đang tổng hợp văn bản thành giọng nói: {output_file}")
        try:
            wav, sr, _ = tts.infer(
                ref_file=ref_file,
                ref_text=ref_text,
                gen_text=SAMPLE_TEXT,
                file_wave=output_file,
                remove_silence=True
            )

            # Kiểm tra kết quả
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                logger.info(f"Tổng hợp thành công: {output_file} ({file_size} bytes)")
                return True
            else:
                logger.error(f"Không tìm thấy file đầu ra: {output_file}")
                return False

        except Exception as e:
            logger.exception(f"Lỗi trong quá trình tổng hợp: {str(e)}")
            return False

    except ImportError as e:
        logger.error(f"Không thể import F5-TTS API: {str(e)}")
        return False
    except Exception as e:
        logger.exception(f"Lỗi kiểm tra F5-TTS API: {str(e)}")
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
    parser.add_argument("--f5tts-api", action="store_true", help="Test F5-TTS using API directly")
    parser.add_argument("--fallback", action="store_true", help="Test Fallback TTS")
    parser.add_argument("--all", action="store_true", help="Test all engines")
    parser.add_argument("--voice", default="female", choices=["female", "male"], help="Voice model to use")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    logger.info(f"Audio files will be saved to: {os.path.abspath(args.output_dir)}")

    if not (args.all or args.f5tts or args.f5tts_api or args.fallback):
        args.all = True

    results = {}

    if args.all or args.f5tts_api:
        results['f5tts_api'] = await test_f5tts_api(args.output_dir, args.voice)

    if args.all or args.f5tts:
        try:
            from utils.tools.tts_test import test_f5tts
            results['f5tts'] = await test_f5tts(args.output_dir, args.voice)
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra F5-TTS provider: {str(e)}")
            results['f5tts'] = False

    if args.all or args.fallback:
        results['fallback'] = await test_fallback_tts(args.output_dir, args.voice)

    logger.info("\n=== KẾT QUẢ KIỂM TRA ===")
    for engine, success in results.items():
        status = "THÀNH CÔNG" if success else "THẤT BẠI"
        logger.info(f"{engine}: {status}")

    if any(results.values()):
        logger.info("Ít nhất một TTS engine đang hoạt động!")
    else:
        logger.error("Tất cả TTS engines đều thất bại!")


if __name__ == "__main__":
    asyncio.run(main())