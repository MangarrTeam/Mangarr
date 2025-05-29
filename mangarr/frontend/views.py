from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from .functions import custom_render, model_field_to_dict
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm
from django.contrib.auth import login
import logging
from plugins.base import NO_THUMBNAIL_URL
from server.settings import CONFIG, LANGUAGE_CODE
from server.settings import LANGUAGES, LANGUAGES_KEYS
from database.users.models import User, UserProfile, RegisterToken
from django.utils.translation import pgettext

logger = logging.getLogger(__name__)


@login_required
def index(request):
    return redirect("monitored_mangas")
    return custom_render(request, "index.html")

@login_required
def my_logout(request):
    logout(request)
    return redirect('index')

def can_register(request) -> bool:
    if not User.objects.exists():
        return True

    token = request.GET.get("token")
    if token is not None and RegisterToken.objects.filter(token=token).exists():
        return True
    
    return False


def register(request):
    if request.method == "GET":
        token = request.GET.get("token")
        if not can_register(request):
            logger.debug("The register token does not exist in database")
            return redirect('login')
        
    if request.method == "POST":
        if not can_register(request):
            logger.debug("The register token does not exist in database")
            return redirect('login')
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            if not User.objects.exists():
                user.is_superuser = True
                user.is_staff = True
            user.save()
            token = request.GET.get("token")
            if token is not None and RegisterToken.objects.filter(token=token).exists():
                logger.debug("The register token found deleting...")
                RegisterToken.objects.get(token=token).delete()
            return redirect("login")
    else:
        form = RegisterForm()

    return custom_render(request, "register.html", {"form": form})


def login_view(request):
    if not User.objects.exists():
        return redirect('register')
    
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('index')

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data['user']
        login(request, user)
        return redirect('index')

    return custom_render(request, "login.html", {"form": form})

import pytz
@permission_required("database_users.can_change_settings")
def settings_view(request):
    settings_dict = {
        'Django': {
            'secret_key': {
                'section_name': pgettext('Django section title', 'frontend.settings.django'),
                'item_name': pgettext('Secret key label', 'frontend.settings.secret_key'),
                'value': CONFIG.get('Django', 'secret_key'),
                'type': 'pass'
            },
            'debug': {
                'section_name': pgettext('Django section title', 'frontend.settings.django'),
                'item_name': pgettext('Debug label', 'frontend.settings.debug'),
                'value': CONFIG.get('Django', 'debug'),
                'type': 'bool'
            },
            'tz': {
                'section_name': pgettext('Django section title', 'frontend.settings.django'),
                'item_name': pgettext('TZ label', 'frontend.settings.tz'),
                'value': CONFIG.get('Django', 'tz'),
                'type': 'choice',
                'choices': [{'key': tzs, 'value': tzs } for tzs in pytz.common_timezones]
            }
        },
        'Plugins': {
            'nsfw_allowed': {
                'section_name': pgettext('Plugins section title', 'frontend.settings.plugins'),
                'item_name': pgettext('NSFW allowed label', 'frontend.settings.nsfw_allowed'),
                'value': CONFIG.get('Plugins', 'nsfw_allowed'),
                'type': 'bool'
            }
        },
        'Networking': {
            'allowed_hosts': {
                'section_name': pgettext('Networking section title', 'frontend.settings.networking'),
                'item_name': pgettext('Allowed hosts label', 'frontend.settings.allowed_hosts'),
                'value': CONFIG.get('Networking', 'allowed_hosts'),
                'type': 'list'
            },
            'csrf_trusted_origins': {
                'section_name': pgettext('Networking section title', 'frontend.settings.networking'),
                'item_name': pgettext('CSRF trusted origins label', 'frontend.settings.csrf_trusted_origins'),
                'value': CONFIG.get('Networking', 'csrf_trusted_origins'),
                'type': 'list'
            }
        },
        'Other': {
            'instance_name': {
                'section_name': pgettext('Other section title', 'frontend.settings.other'),
                'item_name': pgettext('Instance name label', 'frontend.settings.instance_name'),
                'value': CONFIG.get('Other', 'instance_name'),
                'type': 'str'
            }
        },
        'Localization': {
            'locale': {
                'section_name': pgettext('Localization section title', 'frontend.settings.localization'),
                'item_name': pgettext('Locale label', 'frontend.settings.locale'),
                'value': CONFIG.get('Localization', 'locale', fallback=LANGUAGE_CODE, choices=LANGUAGES_KEYS),
                'type': 'choice',
                'choices': [ {'key': l[0], 'value': l[1] } for l in LANGUAGES]
            }
        }
    }

    if request.method == "POST":
        for section, value in settings_dict.items():
            for ikey, item in value.items():
                form_key = f"{section}.{ikey}"
                if form_key in request.POST:
                    values = request.POST.getlist(form_key)
                    if item.get("type") == "choice":
                        v = values[-1]
                        if v not in [l.get("key", LANGUAGE_CODE) for l in item.get("choices", [])]:
                            final_value = LANGUAGE_CODE
                        else:
                            final_value = v
                    elif item.get("type") == "bool":
                        final_value = values[-1]
                    else:
                        final_value = ",".join(values)

                    logging.debug(f'Updating section "{section}" key "{ikey}" with value "{final_value}"')
                    CONFIG.set(section, ikey, final_value)
        CONFIG._write_with_comments()
        return redirect("settings")

    return custom_render(request, "settings.html", {'settings': settings_dict, "config_changed": CONFIG.config_changed()})

@permission_required("database_users.can_change_settings")
def settings_connectors_view(request):
    settings_dict = {
        'Kavita': {
            'address': {
                'section_name': pgettext('Kavita section title', 'frontend.settings_connectors.kavita'),
                'item_name': pgettext('Address label', 'frontend.settings_connectors.address'),
                'value': CONFIG.get('Kavita', 'address'),
                'type': 'text'
            },
            'port': {
                'section_name': pgettext('Kavita section title', 'frontend.settings_connectors.kavita'),
                'item_name': pgettext('Port label', 'frontend.settings_connectors.port'),
                'value': CONFIG.get('Kavita', 'port'),
                'type': 'number'
            },
            'ssl': {
                'section_name': pgettext('Kavita section title', 'frontend.settings_connectors.kavita'),
                'item_name': pgettext('SSL label', 'frontend.settings_connectors.ssl'),
                'value': CONFIG.get('Kavita', 'ssl'),
                'type': 'bool'
            },
            'username': {
                'section_name': pgettext('Kavita section title', 'frontend.settings_connectors.kavita'),
                'item_name': pgettext('Username label', 'frontend.settings_connectors.username'),
                'value': CONFIG.get('Kavita', 'username'),
                'type': 'text'
            },
            'password': {
                'section_name': pgettext('Kavita section title', 'frontend.settings_connectors.kavita'),
                'item_name': pgettext('Password label', 'frontend.settings_connectors.password'),
                'value': CONFIG.get('Kavita', 'password'),
                'type': 'pass'
            },
            'token': {
                'section_name': pgettext('Kavita section title', 'frontend.settings_connectors.kavita'),
                'item_name': pgettext('Token label', 'frontend.settings_connectors.token'),
                'value': CONFIG.get('Kavita', 'token'),
                'type': 'pass'
            },
            'library_id': {
                'section_name': pgettext('Kavita section title', 'frontend.settings_connectors.kavita'),
                'item_name': pgettext('Library ID label', 'frontend.settings_connectors.library_id'),
                'value': CONFIG.getint('Kavita', 'library_id'),
                'type': 'number',
                'tooltip': pgettext('Library ID tooltip', 'frontend.settings_connectors.library_id_tooltip')
            }
        }
    }

    if request.method == "POST":
        for section, value in settings_dict.items():
            for ikey, item in value.items():
                form_key = f"{section}.{ikey}"
                if form_key in request.POST:
                    values = request.POST.getlist(form_key)
                    if item.get("type") == "choice":
                        v = values[-1]
                        if v not in [l.get("key", LANGUAGE_CODE) for l in item.get("choices", [])]:
                            final_value = LANGUAGE_CODE
                        else:
                            final_value = v
                    elif item.get("type") == "bool":
                        final_value = values[-1]
                    else:
                        final_value = ",".join(values)

                    logging.debug(f'Updating section "{section}" key "{ikey}" with value "{final_value}"')
                    CONFIG.set(section, ikey, final_value)
        CONFIG._write_with_comments()
        return redirect("settings_connectors")

    return custom_render(request, "settings_connectors.html", {'settings': settings_dict, "config_changed": CONFIG.config_changed()})

from .forms import UserUpdateForm
from django.contrib.auth.forms import PasswordChangeForm
@login_required
def profile(request):
    if request.method == 'POST':
        formProfile = UserUpdateForm(request.POST, instance=request.user)
        if formProfile.is_valid():
            formProfile.save(commit=True)
            return redirect('profile')
    else:
        formProfile = UserUpdateForm(instance=request.user)

    formPassword = PasswordChangeForm(user=request.user)

    return custom_render(request, "profile.html", {'formProfile': formProfile, 'formPassword': formPassword})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save(commit=True)

    return redirect('profile')


from server.functions import superuser_or_staff_required

@superuser_or_staff_required
def manager_user_list(request):
    users = User.objects.all()
    register_tokens = RegisterToken.objects.all()
    return custom_render(request, "manager/user_list.html", {"users": users, "register_tokens": register_tokens})

@permission_required("database_users.can_invite")
@superuser_or_staff_required
def create_register_token(request):
    RegisterToken().save()
    return redirect('manager_user_list')

from plugins.functions import get_plugins

@permission_required("database_users.can_search")
def manga_search(request):
    plugins = get_plugins()
    plugin_names = [name for _, _, name, _ in plugins]
    return custom_render(request, "manga/search.html", {"plugins": [(category, domain, name, languages, name not in plugin_names) for category, domain, name, languages in plugins]})

from database.manga.models import MangaRequest, Manga

@permission_required("database_users.can_manage_requests")
def manga_requests(request):
    return custom_render(request, "manga/requests.html", {"manga_requests": [{"plugin": r.plugin, "manga": r.variables, "pk": r.pk, "user": r.user or pgettext("User unknown text", "frontend.request_manga.user_unknown")} for r in MangaRequest.objects.all()]})

@login_required
def manga_monitored(request):
    return custom_render(request, "manga/monitored.html", {"mangas": sorted([{"name": m.name.value, "url": m.arguments.get("url"), "cover": m.arguments.get("cover", NO_THUMBNAIL_URL), "pk": m.pk, "plugin": m.get_plugin_display()} for m in Manga.objects.all()], key=lambda x: x["name"])})

@login_required
def manga_view(request, pk):
    if not Manga.objects.filter(pk=pk).exists():
        return redirect("monitored_mangas")
    manga = Manga.objects.get(pk=pk)

    volumes = sorted([{"chapters": sorted([{**model_field_to_dict(ch), "chapter": ch.chapter, "id": ch.id} for ch in v.chapters.all()], key=lambda a: a.get("chapter")), "volume": v.volume, "name": v.name.value, "pages": {"downloaded": len(v.chapters.filter(downloaded=True)), "of": len(v.chapters.all())}, "id": v.id} for v in manga.volumes.all()], key=lambda a: a.get("volume"))
    return custom_render(request, "manga/view.html", {"manga": {**model_field_to_dict(manga), "cover": manga.arguments.get("cover", NO_THUMBNAIL_URL)}, "volumes": volumes})