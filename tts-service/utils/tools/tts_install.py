import os
import sys
import subprocess
import tempfile
import shutil
import logging
import argparse
from pathlib import Path

sys.path.insert(0, '/app')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("tts-install")


def run_command(cmd, cwd=None):
    """Run a shell command and log the output."""
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd
    )

    if result.stdout:
        logger.info(f"Command output: {result.stdout}")
    if result.stderr:
        logger.error(f"Command error: {result.stderr}")

    result.check_returncode()
    return result


def install_f5tts():
    """Install F5-TTS and download its models."""
    logger.info("Installing F5-TTS...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            run_command(["git", "clone", "https://github.com/SWivid/F5-TTS.git", temp_dir])

            run_command([sys.executable, "-m", "pip", "install", "-e", "."], cwd=temp_dir)

            logger.info("F5-TTS installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install F5-TTS: {str(e)}")
            return False

    # Download models
    logger.info("Downloading F5-TTS models...")
    models_dir = os.path.expanduser("~/.config/f5-tts/models")
    os.makedirs(models_dir, exist_ok=True)

    female_dir = os.path.join(models_dir, "female")
    male_dir = os.path.join(models_dir, "male")
    os.makedirs(female_dir, exist_ok=True)
    os.makedirs(male_dir, exist_ok=True)

    # Download female model
    try:
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            female_zip = temp_file.name

        run_command([
            "curl", "-L", "-o", female_zip,
            "https://github.com/SWivid/F5-TTS/releases/download/v1.0.0/female.zip"
        ])

        run_command(["unzip", "-o", female_zip, "-d", female_dir])
        os.unlink(female_zip)

        logger.info(f"Female model downloaded to {female_dir}")
    except Exception as e:
        logger.error(f"Failed to download female model: {str(e)}")

    # Download male model
    try:
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            male_zip = temp_file.name

        run_command([
            "curl", "-L", "-o", male_zip,
            "https://github.com/SWivid/F5-TTS/releases/download/v1.0.0/male.zip"
        ])

        run_command(["unzip", "-o", male_zip, "-d", male_dir])
        os.unlink(male_zip)

        logger.info(f"Male model downloaded to {male_dir}")
    except Exception as e:
        logger.error(f"Failed to download male model: {str(e)}")

    return True


def install_viettts():
    """Install VietTTS and download its models."""
    logger.info("Installing VietTTS...")

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            run_command(["git", "clone", "https://github.com/NTT123/vietTTS.git", temp_dir])
            run_command([sys.executable, "-m", "pip", "install", "-e", "."], cwd=temp_dir)

            logger.info("VietTTS installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install VietTTS: {str(e)}")
            return False

    # Download models
    logger.info("Downloading VietTTS models...")
    models_dir = os.path.expanduser("~/.config/vietTTS")
    os.makedirs(models_dir, exist_ok=True)

    female_dir = os.path.join(models_dir, "infore_female")
    os.makedirs(female_dir, exist_ok=True)

    # Download lexicon
    try:
        lexicon_path = os.path.join(models_dir, "lexicon.pkl")
        run_command([
            "curl", "-L", "-o", lexicon_path,
            "https://github.com/NTT123/vietTTS/releases/download/v0.2.0/lexicon.pkl"
        ])
        logger.info(f"Lexicon downloaded to {lexicon_path}")
    except Exception as e:
        logger.error(f"Failed to download lexicon: {str(e)}")

    # Download female model
    try:
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as temp_file:
            female_tar = temp_file.name

        run_command([
            "curl", "-L", "-o", female_tar,
            "https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_female_latest.tar.gz"
        ])

        run_command(["tar", "-xf", female_tar, "-C", female_dir])
        os.unlink(female_tar)

        logger.info(f"Female model downloaded to {female_dir}")
    except Exception as e:
        logger.error(f"Failed to download female model: {str(e)}")

    return True


def install_system_deps():
    logger.info("Installing system dependencies...")

    try:
        run_command(["apt-get", "update"])
        run_command([
            "apt-get", "install", "-y",
            "ffmpeg", "libsndfile1", "espeak-ng", "build-essential",
            "portaudio19-dev", "python3-dev", "git", "curl", "unzip"
        ])

        run_command([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "pip", "setuptools", "wheel"
        ])

        run_command([
            sys.executable, "-m", "pip", "install",
            "numpy", "scipy", "librosa", "torch", "pydub"
        ])

        logger.info("System dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install system dependencies: {str(e)}")
        logger.warning("If you're not running as root, try using sudo.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Install TTS engines for AudioBooks service")
    parser.add_argument("--all", action="store_true", help="Install all components")
    parser.add_argument("--deps", action="store_true", help="Install system dependencies")
    parser.add_argument("--f5tts", action="store_true", help="Install F5-TTS")
    parser.add_argument("--viettts", action="store_true", help="Install VietTTS")

    args = parser.parse_args()

    if not (args.all or args.deps or args.f5tts or args.viettts):
        args.all = True

    if args.all or args.deps:
        try:
            install_system_deps()
        except Exception as e:
            logger.error(f"Error installing system dependencies: {str(e)}")

    if args.all or args.f5tts:
        try:
            install_f5tts()
        except Exception as e:
            logger.error(f"Error installing F5-TTS: {str(e)}")

    if args.all or args.viettts:
        try:
            install_viettts()
        except Exception as e:
            logger.error(f"Error installing VietTTS: {str(e)}")

    logger.info("Installation completed. Run the check script to verify.")


if __name__ == "__main__":
    main()