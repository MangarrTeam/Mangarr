import json, requests, logging
from core.settings import PLUGINS_METADATA_PATH, PLUGIN_REGISTRY, NSFW_ALLOWED, plugins_loaded
from .base import MangaPluginBase
logger = logging.getLogger(__name__)


def get_plugin_choices() -> list[tuple]:
    return [
        (f'{pm["category"]}_{pm["domain"]}', f'{pm["name"]} ({pm["category"]})')
        for pm in get_downloaded_metadata()
        if pm.get("category") and pm.get("domain") and pm.get("name")
    ]

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

import threading
_registry_lock = threading.Lock()
def get_plugin_by_key(key:str, nsfw:bool = False) -> MangaPluginBase:
    plugins_loaded.wait()
    with _registry_lock:
        if key in PLUGIN_REGISTRY:
            return PLUGIN_REGISTRY[key](nsfw)
        
        logger.error(f"Can't find plugin with key {key}")
    return MangaPluginBase(nsfw)
    
def get_plugin(category: str, domain: str, nsfw:bool = False) -> type[MangaPluginBase]:
    return get_plugin_by_key(f'{category}_{domain}', nsfw)

def get_plugins_domains(category: str) -> list:
    plugins_loaded.wait()
    output = set()
    with _registry_lock:
        for key, _ in PLUGIN_REGISTRY.items():
            if key.startswith(category):
                output.add(key.removeprefix(f"{category}_"))
        return list(output)

def get_plugins() -> list:
    plugins_loaded.wait()
    output = []
    with _registry_lock:
        for key, plugin in PLUGIN_REGISTRY.items():
            if key.startswith("core"):
                domain = key.removeprefix("core_")
                output.append(("core", domain, get_plugin_name("core", domain), sorted(plugin.get_languages()), plugin.nsfw_only))
            if key.startswith("community"):
                domain = key.removeprefix("community_")
                output.append(("community", domain, get_plugin_name("community", domain), sorted(plugin.get_languages()), plugin.nsfw_only))
        return output
    
def fetch_repo_manifest(repo):
    try:
        url = f"https://raw.githubusercontent.com/{repo}/main/manifest.json"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f'Failed to fetch manifest for {repo}: {e}')
        return None
    
def get_downloaded_metadata() -> list[dict]:
    with open(PLUGINS_METADATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except FileNotFoundError as e:
            logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
            return []
        except Exception as e:
            logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
            return []
    
def fetch_json_list(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f'Failed to fetch list: {url} - {e}')
        return []