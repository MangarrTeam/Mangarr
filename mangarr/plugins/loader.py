import importlib.util
import inspect
from .base import MangaPluginBase
from server.settings import PLUGINS_DIR

class PluginNotAvailable(Exception): pass
class PluginMissingMethods(Exception): pass

"""
from .loader import load_plugin
plugin = load_plugin("core", "mangarr-test-plugin")
manga = plugin.get_manga()
print(manga)
"""

def load_plugin(category: str, domain: str) -> MangaPluginBase:
    plugin_path = PLUGINS_DIR / category / domain / "__init__.py"
    
    if not plugin_path.exists():
        raise PluginNotAvailable(f"Plugin '{category}.{domain}' not found at {plugin_path}")

    module_name = f"{category}_{domain}_plugin"

    spec = importlib.util.spec_from_file_location(module_name, plugin_path)
    if not spec or not spec.loader:
        raise PluginNotAvailable(f"Cannot create module spec for plugin '{category}.{domain}'")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise PluginNotAvailable(f"Failed to load plugin '{category}.{domain}': {e}")

    plugin_classes = [
        cls for name, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, MangaPluginBase) and cls is not MangaPluginBase and cls.__module__ == module.__name__
    ]
    
    if not plugin_classes:
        raise PluginMissingMethods(f"No class inheriting MangaPluginBase found in plugin '{category}.{domain}'")

    return plugin_classes[0]