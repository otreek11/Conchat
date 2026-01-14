import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger('ConchatWebhooks')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('[{asctime}] [{levelname}]: {message}', style='{')

    # Máximo de 5 MB, 5 backups
    file_handler = RotatingFileHandler('logs/webhooks.log', maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
