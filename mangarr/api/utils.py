from database.manga.models import MangaRequest, Manga
from processes.models import MonitorManga
from database.users.models import UserProfile
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from uuid import uuid4
import threading
from .search_cache import mark_processing, store_result
from plugins.utils import get_plugin

def manga_is_monitored(manga:dict) -> bool:
    url = manga.get("url")
    if url is not None and (Manga.monitor_exist(url) or MonitorManga.objects.filter(url=url).exists()):
        return True
    return False


def manga_is_requested(manga:dict) -> bool:
    url = manga.get("url")
    if url is not None and MangaRequest.request_exist(url):
        return True
    return False

def validate_token(func):
    def wrapper(request):
        token = request.GET.get("token") or request.POST.get("token")
        if token is None:
            return JsonResponse({"error": "Token is not defined"}, status=401)
        if not UserProfile.objects.filter(token=token).exists():
            return JsonResponse({"error": "Token is invalid"}, status=401)
        
        return func(request)
    
    return wrapper


require_DELETE = require_http_methods(["DELETE"])
require_DELETE.__doc__ = "Decorator to require that a view only accepts the DELETE method."

require_GET_PATCH = require_http_methods(["GET", "PATCH"])
require_GET_PATCH.__doc__ = "Decorator to require that a view only accepts the GET and PATCH method."


def start_background_search(query, category, domain, language=None):
    task_id = str(uuid4())
    mark_processing(task_id)

    def worker():
        try:
            plugin = get_plugin(category, domain)
            if language and language in plugin.get_languages():
                manga = plugin.search_manga(query, language)
            else:
                manga = plugin.search_manga(query)
            result = [{**m, "monitored": manga_is_monitored(m), "requested": manga_is_requested(m)} for m in manga]
            store_result(task_id, result)
        except Exception as e:
            store_result(task_id, {"error": f"Error - {e}"})

    threading.Thread(target=worker, daemon=True).start()
    return task_id