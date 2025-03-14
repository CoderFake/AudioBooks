import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from core.config import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        logging.getLogger('asyncio').setLevel(logging.ERROR)

    return logger