import json
from server.settings import PLUGINS_METADATA_PATH, PLUGIN_REGISTRY
from .base import MangaPluginBase
import logging
logger = logging.getLogger(__name__)


def load_metadata():
    with open(PLUGINS_METADATA_PATH) as f:
        return json.load(f)
    
def get_plugin(category: str, domain: str) -> type[MangaPluginBase]:
    key = f"{category}_{domain}"
    if key in PLUGIN_REGISTRY:
        return PLUGIN_REGISTRY[key]
    
    logger.error(f"Can't fint plugin with key {key}")
    return MangaPluginBase
