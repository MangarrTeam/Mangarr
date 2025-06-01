from plugins.base import MangaPluginBase
from typing import Dict
import threading

plugins_loaded = threading.Event()
PLUGIN_REGISTRY: Dict[str, type[MangaPluginBase]] = {}