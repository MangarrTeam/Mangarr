from django.contrib.auth.models import User, Permission
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from core.utils import superuser_or_staff_required, superuser_required
from core.settings import FILE_PATH_ROOT
from database.users.models import UserProfile, RegisterToken
from database.manga.models import Manga, Volume, Chapter, Library
from django.contrib.contenttypes.models import ContentType
from connectors.models import ConnectorBase
from django.utils.translation import gettext_lazy as _, pgettext
from django.contrib.auth.decorators import permission_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json, os
from .utils import manga_is_monitored, manga_is_requested, validate_token, require_DELETE, require_GET_PATCH, start_background_search
from processes.models import MonitorManga, MonitorChapter, EditChapter
from django.db import IntegrityError
from processes.tasks import trigger_monitor
from django.utils.translation import override
from core.settings import LANGUAGE_CODE
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

    custom_codenames = user.profile.get_custom_permissions()
    custom_permissions = Permission.objects.filter(
        content_type=userprofile_ct,
        codename__in=custom_codenames
    )

    all_permissions = set(list(custom_permissions) + list(user_permissions))

    def get_translated_name(perm):
        if perm.content_type == userprofile_ct and perm.codename in custom_codenames:
            with override(LANGUAGE_CODE):
                return pgettext(
                    f"Permission value for '{perm.codename.replace('_', ' ').capitalize()}'",
                    f"permission.{perm.codename}"
                )
        return perm.name

    return JsonResponse({
        "permissions": [
            {"id": perm.id, "name": get_translated_name(perm), "codename": perm.codename, "has": perm in user_permissions}
            for perm in all_permissions
        ]
   })

@superuser_or_staff_required
def get_user_libraries(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    user_libraries = user.profile.allowed_libraries.all()
    all_libraries = Library.objects.all()

    return JsonResponse({
        "libraries": [
            {"id": lib.id, "name": str(lib), "can": lib in user_libraries}
            for lib in all_libraries
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

@superuser_or_staff_required
def update_user_libraries(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, pk=user_id)
        library_str = request.POST.get('libraries')
        library_ids = library_str.split(",") if len(library_str) > 0 else []
        libraries = Library.objects.filter(id__in=library_ids)
        user.profile.allowed_libraries.set(libraries)
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

@superuser_required
def toggle_nsfw_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id).profile
        user.nsfw_allowed = not user.nsfw_allowed
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
@require_DELETE
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        return JsonResponse({"error": "Forbidden"}, status=403)
    user.delete()
    return JsonResponse({'success': True})

@superuser_or_staff_required
@require_DELETE
def delete_token(request, token_id):
    token = get_object_or_404(RegisterToken, id=token_id)
    token.delete()
    return JsonResponse({'success': True})

@permission_required("database_users.can_manage_plugins")
def toggle_pause_downloads(request):
    from core.settings import toggle_download_pause, is_download_paused
    toggle_download_pause()
    return JsonResponse({'success': True, 'paused': is_download_paused()})

from .search_cache import get_result

from plugins.utils import get_plugins_domains
@permission_required("database_users.can_search")
@require_POST
def search_manga_start(request):
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
        return JsonResponse({"error": "Category needs to be 'core' or 'community'"}, status=400)
    domain = data.get("domain")
    if domain is None:
        return JsonResponse({"error": "Missing parameter 'domain'"}, status=400)
    if domain not in get_plugins_domains(category):
        return JsonResponse({"error": "Domain does not exist"}, status=403)
    language = data.get("language")
    
    task_id = start_background_search(query, category, domain, language, request.user.profile.nsfw_allowed)
    
    return JsonResponse({"task_id": task_id})

@permission_required("database_users.can_search")
@require_GET
def search_manga_status(request, task_id):
    result = get_result(task_id)

    if result is None:
        return JsonResponse({"error": "Not found"}, status=404)

    if result.get("status") == "processing":
        return JsonResponse({"processing": True})

    return JsonResponse({"processing": False, "result": result["data"]})

from database.manga.models import MangaRequest

@permission_required("database_users.can_request")
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
        library_id = data.get("library_id")
        if library_id is None:
            return JsonResponse({"error": "Missing parameter 'library_id'"}, status=400)
        library = Library.objects.filter(id=library_id)
        if not library.exists():
            return JsonResponse({"error": "Library with this ID does not exist"}, status=400)
        
        if MangaRequest.has_plugin(category, domain):
            manga_request = MangaRequest()
            manga_request.choose_plugin(category, domain)
            manga_request.library = library.first()
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
    


@permission_required("database_users.can_manage_libraries")
@require_POST
def library_explore_path(request):
    try:
        data = json.loads(request.body)
        path = data.get('path', FILE_PATH_ROOT)
        
        # Security: Normalize and validate the path
        path = os.path.normpath(path)
        root = os.path.normpath(FILE_PATH_ROOT)
        
        # Ensure path starts with root to prevent directory traversal
        if not path.startswith(root):
            return JsonResponse({
                "success": False,
                "error": "Invalid path: outside root directory"
            }, status=403)
        
        # Check if path exists and is a directory
        if not os.path.exists(path):
            return JsonResponse({
                "success": False,
                "error": "Path does not exist"
            }, status=404)
        
        if not os.path.isdir(path):
            return JsonResponse({
                "success": False,
                "error": "Path is not a directory"
            }, status=400)
        
        # List directory contents
        folders = []
        files = []
        
        try:
            entries = os.listdir(path)
        except PermissionError:
            return JsonResponse({
                "success": False,
                "error": "Permission denied to access this directory"
            }, status=403)
        
        for entry in sorted(entries):
            entry_path = os.path.join(path, entry)
            
            # Skip hidden files/folders (starting with .)
            if entry.startswith('.'):
                continue
            
            try:
                if os.path.isdir(entry_path):
                    folders.append({
                        "name": entry,
                        "path": entry_path
                    })
                elif os.path.isfile(entry_path):
                    files.append({
                        "name": entry,
                        "path": entry_path
                    })
            except (PermissionError, OSError):
                # Skip entries we can't access
                continue
        
        return JsonResponse({
            "success": True,
            "current_path": path,
            "folders": folders,
            "files": files
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON in request body"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

    
@permission_required("database_users.can_manage_libraries")
@require_POST
def library_add(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', 'Library')
        path = data.get('path', FILE_PATH_ROOT)

        library = Library.objects.filter(name=name)
        if library.exists():
            return JsonResponse({
                "success": False,
                "error": "Library already exists"
            }, status=409)
        Library.objects.create(name=name, folder=path)

        return JsonResponse({"success": True}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON in request body"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)



@permission_required("database_users.can_manage_libraries")
@require_POST
def library_edit(request, id):
    try:
        data = json.loads(request.body)
        name = data.get('name', 'Library')

        library = Library.objects.filter(id=id)
        if not library.exists():
            return JsonResponse({
                "success": False,
                "error": "Library does not exist"
            }, status=409)
        library.update(name=name)

        return JsonResponse({"success": True}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON in request body"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@permission_required("database_users.can_manage_libraries")
@require_DELETE
def library_delete(request, id):
    try:
        library = Library.objects.filter(id=id)
        if not library.exists():
            return JsonResponse({
                "success": False,
                "error": "Library does not exist"
            }, status=409)
        library.delete()

        return JsonResponse({"success": True}, status=200)
    
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
    
@permission_required("database_users.can_manage_connectors")
@require_POST
def connector_add(request):
    try:
        data = json.loads(request.body)
        parameters = data.get('parameters', {})
        library_id = data.get('library_id')
        type = data.get('type')

        library = Library.objects.filter(id=library_id)
        if not library.exists():
            return JsonResponse({
                "success": False,
                "error": f"Library does not exists"
            }, status=400)
        library = library.first()

        connector_class = ConnectorBase.get_subclass_by_name(type)
        connector = connector_class.objects.filter(library=library)
        if connector.exists():
            return JsonResponse({
                "success": False,
                "error": f"Library {library.name} already have {connector.first().name} connector"
            }, status=409)
        connector_class.objects.create(library=library, **parameters)

        return JsonResponse({"success": True}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON in request body"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@permission_required("database_users.can_manage_connectors")
@require_POST
def connector_edit(request, id):
    try:
        data = json.loads(request.body)
        parameters = data.get('parameters', {})
        library_id = data.get('library_id')

        library = Library.objects.filter(id=library_id)
        if not library.exists():
            return JsonResponse({
                "success": False,
                "error": f"Library does not exists"
            }, status=400)
        library = library.first()

        connector = ConnectorBase.objects.filter(id=id, library=library)
        if not connector.exists():
            return JsonResponse({
                "success": False,
                "error": f"Library {library.name} does not have this {connector.first().name} connector"
            }, status=409)
        connector.update(**parameters)

        return JsonResponse({"success": True}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON in request body"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@permission_required("database_users.can_manage_connectors")
@require_DELETE
def connector_delete(request, id):
    try:
        connector = ConnectorBase.objects.filter(id=id)
        if not connector.exists():
            return JsonResponse({
                "success": False,
                "error": f"Connector does not exist"
            }, status=400)
        connector.delete()

        return JsonResponse({"success": True}, status=200)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

@permission_required("database_users.can_monitor")
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
        library_id = data.get("library_id")
        if library_id is None:
            return JsonResponse({"error": "Missing parameter 'library_id'"}, status=400)
        library = Library.objects.filter(id=library_id)
        if not library.exists():
            return JsonResponse({"error": "Library with this ID does not exist"}, status=400)
        
        plugin_key = f'{category}_{domain}'
        url = data.get("manga", {}).get("url")
        if url is not None:
            MangaRequest.delete_if_exist(url)
        manga = MonitorManga(library=library.first(), plugin=plugin_key, url=url, arguments=data.get("manga"))

        manga.save()
        trigger_monitor()
        return JsonResponse({"success": True}, status=200)
    except Exception as e:
        return JsonResponse({"error": f"Error - {e}"}, status=500)
    
@permission_required("database_users.can_manage_metadata")
@require_GET_PATCH
def edit_manga(request, manga_id):
    try:
        manga = Manga.objects.get(id=manga_id)
    except Manga.DoesNotExist:
        return JsonResponse({'error': "Manga not found"}, status=404)
    
    if request.method == "GET":
        with override(LANGUAGE_CODE):
            return JsonResponse(manga.to_representation())
    
    # PATCH
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': "Invalid JSON."}, status=400)
    
    manga.update_fields(data, force=True)

    with override(LANGUAGE_CODE):
        return JsonResponse({
            "success": True,
            "updated": manga.to_representation()
        })
    
    
@permission_required("database_users.can_manage_metadata")
@require_POST
def request_edit_manga(request, manga_id):
    try:
        manga = Manga.objects.get(id=manga_id)
    except Manga.DoesNotExist:
        return JsonResponse({'error': "Chapter not found"}, status=404)
    
    if all([EditChapter.edit_exist(chapter) for volume in manga.volumes.all() for chapter in volume.chapters.all()]):
        return JsonResponse({'error': "All chapters already requested"}, status=400)
    
    try:
        new_edit_requests = []
        for volume in manga.volumes.all():
            for chapter in volume.chapters.all():
                if not EditChapter.edit_exist(chapter):
                    new_edit_request = EditChapter(chapter=chapter)
                    new_edit_requests.append(new_edit_request)
        EditChapter.objects.bulk_create(new_edit_requests, batch_size=100)

        trigger_monitor()
    except Exception as e:
        logger.error(f"Error - {e}")
        return JsonResponse({"error": e}, status=500)
    
    return JsonResponse({"success": True}, status=200)

@permission_required("database_users.can_manage_metadata")
@require_GET_PATCH
def edit_volume(request, volume_id):
    try:
        volume = Volume.objects.get(id=volume_id)
    except Volume.DoesNotExist:
        return JsonResponse({'error': "Volume not found"}, status=404)

    if request.method == "GET":
        with override(LANGUAGE_CODE):
            return JsonResponse(volume.to_representation())
    
    # PATCH
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': "Invalid JSON."}, status=400)
    
    volume.update_fields(data, force=True)

    with override(LANGUAGE_CODE):
        return JsonResponse({
            "success": True,
            "updated": volume.to_representation()
        })
    
    
@permission_required("database_users.can_manage_metadata")
@require_POST
def request_edit_volume(request, volume_id):
    try:
        volume = Volume.objects.get(id=volume_id)
    except Volume.DoesNotExist:
        return JsonResponse({'error': "Chapter not found"}, status=404)
    
    if all([EditChapter.edit_exist(chapter) for chapter in volume.chapters.all()]):
        return JsonResponse({'error': "All chapters already requested"}, status=400)
    
    try:
        new_edit_requests = []
        for chapter in volume.chapters.all():
            if not EditChapter.edit_exist(chapter):
                new_edit_request = EditChapter(chapter=chapter)
                new_edit_requests.append(new_edit_request)
        EditChapter.objects.bulk_create(new_edit_requests, batch_size=100)
        trigger_monitor()
    except Exception as e:
        logger.error(f"Error - {e}")
        return JsonResponse({"error": e}, status=500)
    
    return JsonResponse({"success": True}, status=200)

@permission_required("database_users.can_manage_metadata")
@require_GET_PATCH
def edit_chapter(request, chapter_id):
    try:
        chapter = Chapter.objects.get(id=chapter_id)
    except Chapter.DoesNotExist:
        return JsonResponse({'error': "Chapter not found"}, status=404)

    if request.method == "GET":
        with override(LANGUAGE_CODE):
            return JsonResponse(chapter.to_representation())
    
    # PATCH
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': "Invalid JSON."}, status=400)
    
    chapter.update_fields(data, force=True)

    with override(LANGUAGE_CODE):
        return JsonResponse({
            "success": True,
            "updated": chapter.to_representation()
        })

@permission_required("database_users.can_manage_metadata")
@require_POST
def request_edit_chapter(request, chapter_id):
    try:
        chapter = Chapter.objects.get(id=chapter_id)
    except Chapter.DoesNotExist:
        return JsonResponse({'error': "Chapter not found"}, status=404)
    
    if EditChapter.edit_exist(chapter):
        return JsonResponse({'error': "Chapter already requested"}, status=400)
    
    try:
        EditChapter.objects.create(chapter=chapter)
        trigger_monitor()
    except Exception as e:
        logger.error(f"Error - {e}")
        return JsonResponse({"error": e}, status=500)
    
    return JsonResponse({"success": True}, status=200)

@permission_required("database_users.can_manage_monitors")
@require_POST
def request_redownload_chapter(request, chapter_id):
    try:
        chapter = Chapter.objects.get(id=chapter_id)
    except Chapter.DoesNotExist:
        return JsonResponse({'error': "Chapter not found"}, status=404)
    
    manga = chapter.volume.manga

    if MonitorChapter.objects.filter(url=chapter.url).exists():
        return JsonResponse({'error': "Chapter redownload already requested"}, status=400)
    
    try:
        monitor = MonitorChapter(
            url=chapter.url,
            manga=manga,
            plugin=manga.plugin,
            arguments=chapter.arguments
            )
        chapter.downloaded = False
        chapter.save()
        monitor.save()
        trigger_monitor()
    except Exception as e:
        logger.error(f"Error - {e}")
        return JsonResponse({"error": e}, status=500)
    
    return JsonResponse({"success": True}, status=200)

@permission_required("database_users.can_manage_monitors")
@require_POST
def transfer_chapter(request, chapter_id, manga_id):
    try:
        chapter = Chapter.objects.get(id=chapter_id)
    except Chapter.DoesNotExist:
        return JsonResponse({'error': "Chapter not found"}, status=404)
    try:
        manga = Manga.objects.get(id=manga_id)
    except Manga.DoesNotExist:
        return JsonResponse({'error': "Manga not found"}, status=404)
    
    try:
        volumes = Volume.objects.filter(manga=manga)
        volume = None
        for v in volumes:
            if v.volume == chapter.volume.volume:
                volume = v
                break
        
        if volume is None:
            ch_volume = chapter.volume
            volume = Volume.objects.create(number=ch_volume.volume, manga=manga)
        chapter.volume = volume
        chapter.save()
        EditChapter.objects.create(chapter=chapter)
        trigger_monitor()
        return JsonResponse({'success': True}, status=200)
    except Exception as e:
        return JsonResponse({'error': f"Error - {e}"}, status=500)

        
    
@permission_required("database_users.can_manage_metadata")
@require_DELETE
def delete_manga(request, manga_id):
    manga = get_object_or_404(Manga, id=manga_id)
    manga.delete()
    return JsonResponse({'success': True})

@permission_required("database_users.can_manage_metadata")
@require_POST
def mass_edit_manga(request, manga_id):
    try:
        manga = Manga.objects.get(id=manga_id)
    except Manga.DoesNotExist:
        return JsonResponse({'error': "Manga not found"}, status=404)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': "Invalid JSON."}, status=400)
    
    field = data.get("field")
    value = data.get("value")

    if field is None or value is None:
        return JsonResponse({
            "error": f"{'Field ' if field is None else ''}{('and Value' if field is None else 'Value') if value is None else '' } can't be None"
        }, status=400)

    allowed_fields = {
        "name": str,
        "description": str,
        "release_date": str,
        "format": int,
        "age_rating": int,
        "isbn": str
    }

    if field not in allowed_fields.keys():
        return JsonResponse({
            "error": f"Field '{field}' is not in allowed list of fields"
        }, status=400)
    
    chapter_to_update = []

    for volume in manga.volumes.all():
        for chapter in volume.chapters.all():
            try:
                target_type = allowed_fields.get(field, str)
                chapter_field = getattr(chapter, field)
                if hasattr(chapter_field, "set_value"):
                    chapter_field.set_value(target_type(value), force=True)
                    chapter_field.lock()
                    chapter_to_update.append(chapter)
            except Exception as e:
                logger.error(f"Error - {e}")

    Chapter.objects.bulk_update(chapter_to_update, [field])
    
    return JsonResponse({
        "success": True
    }, status=200)

@permission_required("database_users.can_manage_requests")
@require_POST
def approve_manga_request(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Error - {e}"}, status=500)
    pk = data.get("pk")
    if pk is None:
        return JsonResponse({"error": "PK needs to be difined"}, status=400)
    try:
        manga_request = MangaRequest.objects.get(pk=pk)
        if manga_request is None:
            return JsonResponse({"error": "Manga request not found"}, status=400)
        plugin = manga_request.plugin
        url = manga_request.variables.get("url")
        if url is None:
            raise TypeError("URL is None")
        library_id = data.get("library", manga_request.library.id)
        library = Library.objects.filter(id=library_id)
        if not library.exists():
            return JsonResponse({"error": "Library does not exist"}, status=400)
        
        MonitorManga(library=library.first(), plugin=plugin, url=url, arguments=manga_request.variables).save()

        manga_request.delete()
        trigger_monitor()
        return JsonResponse({"success": True}, status=200)
    except IntegrityError as e:
        MangaRequest.objects.get(pk=pk).delete()
        return JsonResponse({"error": f"Error - {e}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Error - {e}"}, status=500)

@permission_required("database_users.can_manage_requests")
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