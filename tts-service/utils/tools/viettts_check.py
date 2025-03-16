import os
import sys
import importlib.util
import subprocess
import logging

sys.path.insert(0, '/app')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("viettts-check")


def check_viettts():
    logger.info("Checking VietTTS...")

    viettts_spec = importlib.util.find_spec("vietTTS")
    if viettts_spec is None:
        logger.error("VietTTS is NOT installed")
        return False

    logger.info(f"VietTTS is installed at: {viettts_spec.origin}")

    model_dir = os.path.expanduser("~/.config/vietTTS")
    if not os.path.exists(model_dir):
        logger.error(f"VietTTS model directory not found: {model_dir}")
        return False

    female_model = os.path.join(model_dir, "infore_female")
    male_model = os.path.join(model_dir, "infore_male")
    lexicon = os.path.join(model_dir, "lexicon.pkl")

    if os.path.exists(female_model):
        logger.info(f"VietTTS female model found at: {female_model}")
        config_file = os.path.join(female_model, "config.json")
        if os.path.exists(config_file):
            logger.info("VietTTS female model config file found")
        else:
            logger.error("VietTTS female model config file NOT found")
    else:
        logger.error(f"VietTTS female model NOT found at: {female_model}")

    if os.path.exists(male_model):
        logger.info(f"VietTTS male model found at: {male_model}")
        config_file = os.path.join(male_model, "config.json")
        if os.path.exists(config_file):
            logger.info("VietTTS male model config file found")
        else:
            logger.error("VietTTS male model config file NOT found")
    else:
        logger.error(f"VietTTS male model NOT found at: {male_model}")

    if os.path.exists(lexicon):
        logger.info(f"VietTTS lexicon file found at: {lexicon}")
    else:
        logger.error(f"VietTTS lexicon file NOT found at: {lexicon}")

    try:
        import vietTTS
        logger.info("Successfully imported vietTTS module")

        # Try to run the command line tool
        result = subprocess.run(
            ["python", "-m", "vietTTS.synthesize", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            logger.info("VietTTS command line tool is available")
        else:
            logger.error("VietTTS command line tool is NOT working")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")

        return True
    except Exception as e:
        logger.error(f"Error importing vietTTS module: {str(e)}")
        return False


def check_system_deps():
    logger.info("Checking system dependencies...")

    # Check ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            logger.info("ffmpeg is installed")
        else:
            logger.error("ffmpeg is NOT installed")
    except Exception:
        logger.error("ffmpeg is NOT installed or not in PATH")

    try:
        import torch
        logger.info(f"PyTorch is installed: version {torch.__version__}")

        cuda_available = torch.cuda.is_available()
        logger.info(f"CUDA is {'available' if cuda_available else 'NOT available'}")

        if cuda_available:
            logger.info(f"CUDA version: {torch.version.cuda}")

    except ImportError:
        logger.error("PyTorch is NOT installed")

    try:
        import torchaudio
        logger.info(f"torchaudio is installed: version {torchaudio.__version__}")
    except ImportError:
        logger.error("torchaudio is NOT installed")

    try:
        import librosa
        logger.info(f"librosa is installed: version {librosa.__version__}")
    except ImportError:
        logger.error("librosa is NOT installed")

    try:
        import pydub
        logger.info(f"pydub is installed")
    except ImportError:
        logger.error("pydub is NOT installed")


def main():
    logger.info("===== VietTTS System Check =====")

    check_system_deps()

    logger.info("\n===== VietTTS Check =====")
    viettts_ok = check_viettts()

    logger.info("\n===== Summary =====")
    logger.info(f"VietTTS: {'OK' if viettts_ok else 'FAIL'}")

    if viettts_ok:
        logger.info("VietTTS engine is available")
    else:
        logger.error("VietTTS engine is NOT available")


if __name__ == "__main__":
    main()