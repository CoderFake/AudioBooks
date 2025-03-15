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

logger = logging.getLogger("tts-check")


def check_f5tts():
    logger.info("Checking F5-TTS...")

    f5tts_spec = importlib.util.find_spec("f5_tts")
    if f5tts_spec is None:
        logger.error("F5-TTS is NOT installed")
        return False

    logger.info(f"F5-TTS is installed at: {f5tts_spec.origin}")

    model_dir = os.path.expanduser("~/.config/f5-tts/models")
    if not os.path.exists(model_dir):
        logger.error(f"F5-TTS model directory not found: {model_dir}")
        return False

    female_model = os.path.join(model_dir, "female")
    male_model = os.path.join(model_dir, "male")

    if os.path.exists(female_model):
        logger.info(f"F5-TTS female model found at: {female_model}")
        config_file = os.path.join(female_model, "config.json")
        if os.path.exists(config_file):
            logger.info("F5-TTS female model config file found")
        else:
            logger.error("F5-TTS female model config file NOT found")
    else:
        logger.error(f"F5-TTS female model NOT found at: {female_model}")

    if os.path.exists(male_model):
        logger.info(f"F5-TTS male model found at: {male_model}")
        config_file = os.path.join(male_model, "config.json")
        if os.path.exists(config_file):
            logger.info("F5-TTS male model config file found")
        else:
            logger.error("F5-TTS male model config file NOT found")
    else:
        logger.error(f"F5-TTS male model NOT found at: {male_model}")

    try:
        import f5_tts
        logger.info("Successfully imported f5_tts module")
        return True
    except Exception as e:
        logger.error(f"Error importing f5_tts module: {str(e)}")
        return False


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
        return True
    except Exception as e:
        logger.error(f"Error importing vietTTS module: {str(e)}")