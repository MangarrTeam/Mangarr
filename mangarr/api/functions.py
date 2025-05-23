from database.manga.models import MangaRequest, Manga
from database.users.models import UserProfile
from django.http import JsonResponse


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

def validate_token(func):
    def wrapper(request):
        token = request.GET.get("token")
        if token is None:
            return JsonResponse({"error": "Token is not defined"}, status=401)
        if not UserProfile.objects.filter(token=token).exists():
            return JsonResponse({"error": "Token is invalid"}, status=401)
        
        return func(request)
    
    return wrapper