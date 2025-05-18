import threading
import time
from plugins.manager import update_metadata
import logging
logger = logging.getLogger(__name__)

def background_update():
    while True:
        logger.info("Updating plugin metadata...")
        update_metadata()
        time.sleep(86400)  # 24h
