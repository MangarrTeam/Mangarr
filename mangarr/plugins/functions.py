import json
from server.settings import PLUGINS_METADATA_PATH, PLUGIN_REGISTRY
from .base import MangaPluginBase
import logging
logger = logging.getLogger(__name__)


def load_metadata():
    try:
        with open(PLUGINS_METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
        return []
    except Exception as e:
        logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
        return []
    
def get_plugin_name(category: str, domain: str) -> str:
    metadatas = load_metadata()
    for metadata in metadatas:
        c = metadata.get("category")
        d = metadata.get("domain")
        if c is not None and d is not None and c == category and d == domain:
            name = metadata.get("name")
            return name if name is not None else d
    return domain
    
def get_plugin(category: str, domain: str) -> type[MangaPluginBase]:
    key = f"{category}_{domain}"
    if key in PLUGIN_REGISTRY:
        return PLUGIN_REGISTRY[key]
    
    logger.error(f"Can't find plugin with key {key}")
    return MangaPluginBase

def get_plugins_domains(category: str) -> list:
    output = set()
    for key, _ in PLUGIN_REGISTRY.items():
        if key.startswith(category):
            output.add(key.removeprefix(f"{category}_"))
    return list(output)

def get_plugins() -> list:
    output = []
    for key, plugin in PLUGIN_REGISTRY.items():
        if key.startswith("core"):
            domain = key.removeprefix("core_")
            output.append(("core", domain, get_plugin_name("core", domain), sorted(plugin.get_languages())))
        if key.startswith("community"):
            domain = key.removeprefix("community_")
            output.append(("community", domain, get_plugin_name("community", domain), sorted(plugin.get_languages())))
    return output