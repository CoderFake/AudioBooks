import os
import sys
import subprocess
import tempfile
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

logger = logging.getLogger("viettts-install")


def run_command(cmd, cwd=None):
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


def install_system_deps():
    logger.info("Installing system dependencies...")

    try:
        run_command(["apt-get", "update"])
        run_command([
            "apt-get", "install", "-y",
            "ffmpeg", "libsndfile1", "python3-dev", "git", "curl", "unzip",
            "build-essential"
        ])

        run_command([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "pip", "setuptools", "wheel"
        ])

        run_command([
            sys.executable, "-m", "pip", "install",
            "numpy", "scipy", "librosa", "pydub"
        ])

        logger.info("System dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install system dependencies: {str(e)}")
        logger.warning("If you're not running as root, try using sudo.")
        return False


def install_viettts():
    """Install VietTTS and download its models."""
    logger.info("Installing VietTTS...")

    # Check if VietTTS is already installed
    try:
        import vietTTS
        logger.info(f"VietTTS is already installed at: {vietTTS.__file__}")
    except ImportError:
        logger.info("VietTTS is not installed, installing now...")

        # Clone and install VietTTS
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                run_command(["git", "clone", "https://github.com/NTT123/vietTTS.git", temp_dir])
                run_command([sys.executable, "-m", "pip", "install", "-e", "."], cwd=temp_dir)
                logger.info("VietTTS installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Could not install VietTTS: {str(e)}")
                return False

    # Download models
    logger.info("Downloading VietTTS models...")
    models_dir = os.path.expanduser("~/.config/vietTTS")
    os.makedirs(models_dir, exist_ok=True)

    female_dir = os.path.join(models_dir, "infore_female")
    male_dir = os.path.join(models_dir, "infore_male")
    os.makedirs(female_dir, exist_ok=True)
    os.makedirs(male_dir, exist_ok=True)

    lexicon_path = os.path.join(models_dir, "lexicon.pkl")
    female_config = os.path.join(female_dir, "config.json")
    male_config = os.path.join(male_dir, "config.json")

    # Download lexicon if it doesn't exist
    if not os.path.exists(lexicon_path):
        try:
            run_command([
                "curl", "-L", "-o", lexicon_path,
                "https://github.com/NTT123/vietTTS/releases/download/v0.2.0/lexicon.pkl"
            ])
            logger.info(f"Lexicon downloaded to {lexicon_path}")
        except Exception as e:
            logger.error(f"Could not download lexicon: {str(e)}")

    # Download female model if it doesn't exist
    if not os.path.exists(female_config):
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
            logger.error(f"Could not download female model: {str(e)}")

    # Download male model if it doesn't exist
    if not os.path.exists(male_config):
        try:
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as temp_file:
                male_tar = temp_file.name

            run_command([
                "curl", "-L", "-o", male_tar,
                "https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_male_latest.tar.gz"
            ])

            run_command(["tar", "-xf", male_tar, "-C", male_dir])
            os.unlink(male_tar)

            logger.info(f"Male model downloaded to {male_dir}")
        except Exception as e:
            logger.error(f"Could not download male model: {str(e)}")

    # Verify installation
    try:
        import vietTTS
        logger.info(f"VietTTS installed successfully at: {vietTTS.__file__}")

        if os.path.exists(female_config):
            logger.info(f"Female model is available")

        if os.path.exists(male_config):
            logger.info(f"Male model is available")

        if os.path.exists(lexicon_path):
            logger.info(f"Lexicon is available")

        return True
    except ImportError as e:
        logger.error(f"Error importing VietTTS after installation: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Install VietTTS for AudioBooks service")
    parser.add_argument("--deps", action="store_true", help="Install system dependencies")
    parser.add_argument("--models", action="store_true", help="Install VietTTS models only")
    parser.add_argument("--all", action="store_true", help="Install everything")

    args = parser.parse_args()

    if not (args.all or args.deps or args.models):
        args.all = True

    if args.all or args.deps:
        install_system_deps()

    if args.all or args.models:
        install_viettts()

    logger.info("Installation completed. Run the check script to verify.")


if __name__ == "__main__":
    main()