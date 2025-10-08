import json
import time
from plugins.manager import update_metadata
from core.settings import PLUGIN_REGISTRY, PLUGINS_METADATA_PATH, plugins_loaded
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

def background_update():
    from core.thread_manager import stop_event
    next_update = None
    while not stop_event.is_set():
        if next_update is None or next_update <= datetime.now():
            logger.info("Updating plugin metadata...")
            update_metadata()
            next_update = datetime.now() + timedelta(days=1)    # Set the next update to next day
        time.sleep(10)  # 10 seconds

from .loader import load_plugin
from .base import MangaPluginBase
def load_downloaded_plugins():
    logger.info("Loading downloaded plugins...")

    try:
        with open(PLUGINS_METADATA_PATH, "r", encoding="utf-8") as f:
            metadatas = json.load(f)
    except FileNotFoundError as e:
        logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
        metadatas = []
    except Exception as e:
        logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
        metadatas = []

    for metadata in metadatas:
        if metadata["downloaded_version"] is not None:
            load_and_register_plugin(metadata["category"], metadata["domain"])

    logger.info("Plugins loaded!")
    plugins_loaded.set()

import threading
_registry_lock = threading.Lock()
def load_and_register_plugin(category: str, domain: str) -> None:
    key = f"{category}_{domain}"

    with _registry_lock:
        try:
            plugin_class = load_plugin(category, domain)
        except Exception as e:
            logger.error(f"Error occured while trying to load plugin {category}.{domain} - {e}")
        else:
            PLUGIN_REGISTRY[key] = plugin_class