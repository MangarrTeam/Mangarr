import json
import time
from plugins.manager import update_metadata
from server.settings import PLUGIN_REGISTRY
import logging
logger = logging.getLogger(__name__)

stop_event = None

def background_update():
    while not stop_event.is_set():
        logger.info("Updating plugin metadata...")
        update_metadata()
        time.sleep(86400)  # 24h

from server.settings import PLUGINS_METADATA_PATH
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
        metadata = []

    for metadata in metadatas:
        if metadata["downloaded_version"] is not None:
            load_and_register_plugin(metadata["category"], metadata["domain"])

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