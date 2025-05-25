from django.contrib.auth.models import User, Permission
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from server.functions import superuser_or_staff_required, superuser_required
from database.users.models import UserProfile, RegisterToken
from database.manga.models import Manga, Volume, Chapter
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import permission_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .functions import manga_is_monitored, manga_is_requested, validate_token
from server.settings import NSFW_ALLOWED
from processes.models import MonitorManga
from django.db import IntegrityError
from processes.tasks import trigger_monitor
import logging
logger = logging.getLogger(__name__)


# Create your views here.
@validate_token
def search(request):
    query:str = request.GET.get("query")

    mangas = []
    volumes = []
    chapters = []

    for manga in Manga.objects.all():
        if query.lower() in manga.name.value.lower():
            mangas.append(manga.json_serialized())

    for volume in Volume.objects.all():
        if query.lower() in volume.name.value.lower():
            volumes.append(volume.json_serialized())

    for chapter in Chapter.objects.all():
        if query.lower() in chapter.name.value.lower():
            chapters.append(chapter.json_serialized())

    return JsonResponse({"mangas": mangas, "volumes": volumes, "chapters": chapters})

@csrf_exempt
@require_POST
@validate_token
def regenerate_token_view(request):
    token = UserProfile.objects.get(token=request.GET.get("token")).regenerate_token()
    return JsonResponse(data={"success": True, "token": token})


@superuser_or_staff_required
def get_user_permissions(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user_permissions = user.user_permissions.all()
    userprofile_ct = ContentType.objects.get_for_model(UserProfile)
    custom_permissions = Permission.objects.filter(
        content_type=userprofile_ct,
        codename__in=user.profile.get_custom_permissions()
    )
    all_permissions = set(list(custom_permissions) + list(user_permissions))

    return JsonResponse({
        "permissions": [
            {"id": perm.id, "name": _(perm.name), "codename": perm.codename, "has": perm in user_permissions}
            for perm in all_permissions
        ]
   })

@superuser_or_staff_required
def update_user_permissions(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, pk=user_id)
        permission_str = request.POST.get('permissions')
        permission_ids = permission_str.split(",") if len(permission_str) > 0 else []
        permissions = Permission.objects.filter(id__in=permission_ids)
        user.user_permissions.set(permissions)
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@superuser_required
def toggle_staff_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            return JsonResponse({"error": "Forbidden"}, status=403)
        user.is_staff = not user.is_staff
        user.save()
        source = request.POST.get("zource")
        if source is None:
            source = 'index'
        try:
            reverse(source)
        except:
            source = 'index'

        return redirect(source)
    return JsonResponse({"error": "Forbidden"}, status=400)

@superuser_or_staff_required
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            return JsonResponse({"error": "Forbidden"}, status=403)
        user.delete()
        return JsonResponse({'success': True})
    return JsonResponse({"error": "Forbidden"}, status=400)

@superuser_or_staff_required
def delete_token(request, token_id):
    if request.method == 'POST':
        token = get_object_or_404(RegisterToken, id=token_id)
        token.delete()
        return JsonResponse({'success': True})
    return JsonResponse({"error": "Forbidden"}, status=400)

@permission_required("database.can_manage_plugins")
def toggle_pause_downloads(request):
    from server.settings import toggle_download_pause, is_download_paused
    toggle_download_pause()
    return JsonResponse({'success': True, 'paused': is_download_paused()})


from plugins.functions import get_plugin, get_plugins_domains
@permission_required("database.can_search")
@require_POST
def search_manga(request):
    try:
        data = json.loads(request.body)
    except Exception as e:
        return JsonResponse({"error": f"Error - {e}"}, status=500)
    query = data.get("query")
    if query is None:
        return JsonResponse({"error": "Missing parameter 'query'"}, status=400)
    category = data.get("category")
    if category is None:
        return JsonResponse({"error": "Missing parameter 'category'"}, status=400)
    if category not in ["core", "community"]:
        return JsonResponse({"error": "Category needs to be 'core' or 'cummunity'"}, status=400)
    domain = data.get("domain")
    if domain is None:
        return JsonResponse({"error": "Missing parameter 'domain'"}, status=400)
    if domain not in get_plugins_domains(category):
        return JsonResponse({"error": "Domain does not exist"}, status=403)
    try:
        plugin = get_plugin(category, domain)
        language = data.get("language")
        if language is not None and language in plugin.get_languages():
            manga = plugin.search_manga(query, language)
        else:
            manga = plugin.search_manga(query)
        return JsonResponse([{**m, "monitored": manga_is_monitored(m), "requested": manga_is_requested(m)} for m in manga], safe=False)
    except Exception as e:
        print(f"Can't print manga - {e}")
        return JsonResponse({"error": f"Error - {e}"}, status=500)

    

from database.manga.models import MangaRequest

@permission_required("database.can_request")
@require_POST
def request_manga(request):
    try:
        data = json.loads(request.body)
        category = data.get("category")
        if category is None:
            return JsonResponse({"error": "Missing parameter 'category'"}, status=400)
        if category not in ["core", "community"]:
            return JsonResponse({"error": "Category needs to be 'core' or 'cummunity'"}, status=400)
        domain = data.get("domain")
        if domain is None:
            return JsonResponse({"error": "Missing parameter 'domain'"}, status=400)
        if domain not in get_plugins_domains(category):
            return JsonResponse({"error": "Domain does not exist"}, status=403)
        
        if MangaRequest.has_plugin(category, domain):
            manga_request = MangaRequest()
            manga_request.choose_plugin(category, domain)
            manga_request.variables = data.get("manga")
            manga_request.user = request.user

            if manga_request.variables is None or manga_request.variables.get("url") is None:
                return JsonResponse({"error": f"Request needs at least 'url' in variables ('manga')"}, status=500)
            
            if MangaRequest.request_exist(manga_request.variables.get("url")):
                return JsonResponse({"error": "The request for this item already exists"}, status=409)

            try:
                manga_request.save()
            except Exception as e:
                return JsonResponse({"error": f"Error - {e}"}, status=500)

            return JsonResponse({"success": True}, status=200)


        return JsonResponse({"error": f"There is no plugin with these category: {category} and domain: {domain}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Error - {e}"}, status=500)
    

@permission_required("database.can_monitor")
@require_POST
def monitor_manga(request):
    try:
        data = json.loads(request.body)
        category = data.get("category")
        if category is None:
            return JsonResponse({"error": "Missing parameter 'category'"}, status=400)
        if category not in ["core", "community"]:
            return JsonResponse({"error": "Category needs to be 'core' or 'cummunity'"}, status=400)
        domain = data.get("domain")
        if domain is None:
            return JsonResponse({"error": "Missing parameter 'domain'"}, status=400)
        if domain not in get_plugins_domains(category):
            return JsonResponse({"error": "Domain does not exist"}, status=403)
        
        plugin_key = f'{category}_{domain}'
        url = data.get("manga", {}).get("url")
        if url is not None:
            MangaRequest.delete_if_exist(url)
        manga = MonitorManga(plugin=plugin_key, url=url, arguments=data.get("manga"))

        manga.save()
        trigger_monitor()
        return JsonResponse({"success": True}, status=200)
    except Exception as e:
        return JsonResponse({"error": f"Error - {e}"}, status=500)

@permission_required("database.can_manage_requests")
@require_POST
def approve_manga_request(request):
    pk = request.headers.get("pk")
    if pk is None:
        return JsonResponse({"error": "PK needs to be difined"}, status=400)
    try:
        manga_request = MangaRequest.objects.get(pk=pk)
        plugin = manga_request.plugin
        url = manga_request.variables.get("url")
        if url is None:
            raise TypeError("URL is None")
        
        MonitorManga(plugin=plugin, url=url, arguments=manga_request.variables).save()

        manga_request.delete()
        trigger_monitor()
        return JsonResponse({"success": True}, status=200)
    except IntegrityError as e:
        MangaRequest.objects.get(pk=pk).delete()
        return JsonResponse({"error": f"Error - {e}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Error - {e}"}, status=500)

@permission_required("database.can_manage_requests")
@require_POST
def deny_manga_request(request):
    pk = request.headers.get("pk")
    if pk is None:
        return JsonResponse({"error": "PK needs to be difined"}, status=400)
    
    try:
        manga_request = MangaRequest.objects.get(pk=pk)
        manga_request.delete()
    except Exception as e:    
        return JsonResponse({"error": f"Error - {e}"}, status=500)

    return JsonResponse({"success": True}, status=200)