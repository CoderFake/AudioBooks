#!/usr/bin/env python3
import os
import sys
import argparse
import tempfile
import asyncio
import logging
import subprocess
from datetime import datetime

sys.path.insert(0, '/app')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("viettts-test")

SAMPLE_TEXT = """
Xin chào! Đây là bài kiểm tra hệ thống chuyển đổi văn bản thành giọng nói.
Tiếng Việt có nhiều dấu và âm thanh đặc biệt.
Hệ thống TTS cần phát âm chính xác các từ, cụm từ và câu tiếng Việt.
"""


async def test_viettts(output_dir, voice_model="female"):
    logger.info(f"Testing VietTTS with {voice_model} voice...")

    try:
        # Import VietTTS provider
        from services.tts.vietTTS_provider import VietTTSProvider

        # Create provider instance
        provider = VietTTSProvider(voice_model)

        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"viettts_test_{voice_model}_{timestamp}.wav")

        # Synthesize speech
        logger.info(f"Synthesizing speech to {output_file}")
        await provider.synthesize(SAMPLE_TEXT, output_file)

        # Check result
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            logger.info(f"Speech synthesized successfully: {output_file} ({file_size} bytes)")
            return True
        else:
            logger.error(f"Output file was not created: {output_file}")
            return False

    except Exception as e:
        logger.exception(f"Error testing VietTTS: {str(e)}")
        return False


async def test_vietTTS_command_line(output_dir, voice_model="female"):
    logger.info(f"Testing VietTTS command line with {voice_model} voice...")

    try:
        # Create temporary text file
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', encoding='utf-8', delete=False) as f:
            text_file = f.name
            f.write(SAMPLE_TEXT)

        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"viettts_cmd_test_{voice_model}_{timestamp}.wav")

        # Create command
        cmd = [
            "python", "-m", "vietTTS.synthesize",
            "--input", text_file,
            "--output", output_file,
            "--model", f"infore_{voice_model}"
        ]

        # Run command
        logger.info(f"Running command: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if stdout:
            logger.info(f"Command output: {stdout.decode()}")
        if stderr:
            logger.error(f"Command error: {stderr.decode()}")

        # Check result
        if process.returncode == 0 and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            logger.info(f"Speech synthesized successfully: {output_file} ({file_size} bytes)")
            return True
        else:
            logger.error(f"Command failed with exit code {process.returncode}")
            return False

    except Exception as e:
        logger.exception(f"Error testing VietTTS command line: {str(e)}")
        return False
    finally:
        # Clean up
        if 'text_file' in locals() and os.path.exists(text_file):
            os.unlink(text_file)


async def test_fallback_tts(output_dir, voice_model="female"):
    logger.info("Testing Fallback TTS...")

    try:
        # Import provider
        from services.tts.fallback_provider import FallbackTTSProvider

        # Create provider instance
        provider = FallbackTTSProvider(voice_model)

        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"fallback_test_{voice_model}_{timestamp}.wav")

        # Synthesize speech
        logger.info(f"Generating audio with Fallback TTS to {output_file}")
        await provider.synthesize(SAMPLE_TEXT, output_file)

        # Check result
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
    parser = argparse.ArgumentParser(description="Test VietTTS")
    parser.add_argument("--output-dir", default="./test_output", help="Directory to save test audio files")
    parser.add_argument("--provider", action="store_true", help="Test VietTTS provider")
    parser.add_argument("--command-line", action="store_true", help="Test VietTTS command line")
    parser.add_argument("--fallback", action="store_true", help="Test Fallback TTS")
    parser.add_argument("--all", action="store_true", help="Test all engines")
    parser.add_argument("--voice", default="female", choices=["female", "male"], help="Voice model to use")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    logger.info(f"Audio files will be saved to: {os.path.abspath(args.output_dir)}")

    if not (args.all or args.provider or args.command_line or args.fallback):
        args.all = True

    results = {}

    if args.all or args.provider:
        results['provider'] = await test_viettts(args.output_dir, args.voice)

    if args.all or args.command_line:
        results['command_line'] = await test_vietTTS_command_line(args.output_dir, args.voice)

    if args.all or args.fallback:
        results['fallback'] = await test_fallback_tts(args.output_dir, args.voice)

    logger.info("\n=== TEST RESULTS ===")
    for engine, success in results.items():
        status = "SUCCESS" if success else "FAILURE"
        logger.info(f"{engine}: {status}")

    if any(results.values()):
        logger.info("At least one TTS engine is working!")
    else:
        logger.error("All TTS engines failed!")


if __name__ == "__main__":
    asyncio.run(main())