from .app import *
from logger import logger


logger.info("Initializing Server...")
app = init_app()
logger.info("Server started!")
