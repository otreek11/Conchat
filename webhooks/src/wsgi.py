from app import init_app
from logger import logger

logger.info("Initializing Webhooks Server via WSGI...")
app = init_app()
logger.info("Webhooks Server initialized!")
