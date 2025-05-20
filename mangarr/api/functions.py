from database.models import MangaRequest


def manga_is_monitored(manga:dict) -> bool:
    return False


def manga_is_requested(manga:dict) -> bool:
    url = manga.get("url")
    if url is not None and MangaRequest.request_exist(url):
        return True
    return False