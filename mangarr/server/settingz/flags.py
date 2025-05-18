from django.core.cache import cache

def is_download_paused() -> bool:
    return cache.get('pause_downloads', False)


def toggle_download_pause() -> None:
    cache.set('pause_downloads', not is_download_paused())