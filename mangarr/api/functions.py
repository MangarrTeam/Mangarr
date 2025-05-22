from database.manga.models import MangaRequest, Manga


def manga_is_monitored(manga:dict) -> bool:
    url = manga.get("url")
    if url is not None and Manga.monitor_exist(url):
        return True
    return False


def manga_is_requested(manga:dict) -> bool:
    url = manga.get("url")
    if url is not None and MangaRequest.request_exist(url):
        return True
    return False