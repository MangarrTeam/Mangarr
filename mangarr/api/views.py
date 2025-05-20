from django.contrib.auth.models import User, Permission
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from server.functions import superuser_or_staff_required, superuser_required
from database.models import UserProfile, RegisterToken
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_POST
import json
from .functions import manga_is_monitored, manga_is_requested
from server.settings import NSFW_ALLOWED
import logging
logger = logging.getLogger(__name__)

# Create your views here.
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
    if request.method == "POST":
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
            plugin = get_plugin(category, domain)()
            language = data.get("language")
            if language is not None and language in plugin.get_languages():
                manga = plugin.search_manga(query, NSFW_ALLOWED, language)
            else:
                manga = plugin.search_manga(query, NSFW_ALLOWED)
            monitored_manga = ["https://mangadex.org/title/ffe69cc2-3f9e-4eab-a7f7-c963cea9ec25"]
            return JsonResponse([{**m, "monitored": manga_is_monitored(m), "requested": manga_is_requested(m)} for m in manga], safe=False)
        except Exception as e:
            print(f"Can't print manga - {e}")

    return JsonResponse({"error": "Error"}, status=500)
    

from database.models import MangaRequest

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
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(data)
        except Exception as e:
            return JsonResponse({"error": f"Error - {e}"}, status=500)
    logger.info("Tried to monitor manga TBD")
    return JsonResponse({"error": "Temp success"}, status=200)


@permission_required("database.can_manage_requests")
@require_POST
def approve_manga_request(request):
    pk = request.headers.get("pk")
    if pk is None:
        return JsonResponse({"error": "PK needs to be difined"}, status=400)
    
    try:
        manga_request = MangaRequest.objects.get(pk=pk)
        logger.info("Needs to do approve.")
        #manga_request.delete()
    except Exception as e:    
        return JsonResponse({"error": f"Error - {e}"}, status=500)

    return JsonResponse({"success": True}, status=200)


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