from django.core.cache import cache

def is_download_paused() -> bool:
    return cache.get('pause_downloads', False)


def toggle_download_pause() -> None:
    cache.set('pause_downloads', not is_download_paused())

def plugin_changed() -> None:
    cache.set('plugin_changed', True)


def plugin_change_state() -> bool:
    return cache.get('plugin_changed', False)