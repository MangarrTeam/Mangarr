from plugins.base import MangaPluginBase
from typing import Dict

PLUGIN_REGISTRY: Dict[str, type[MangaPluginBase]] = {}