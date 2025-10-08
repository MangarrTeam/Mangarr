from django.core.cache import cache

def plugin_changed() -> None:
    cache.set('plugin_changed', True)


def plugin_change_state() -> bool:
    return cache.get('plugin_changed', False)