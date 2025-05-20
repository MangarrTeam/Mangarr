from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from .functions import custom_render
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm
from django.contrib.auth import login
from database.models import RegisterToken
import logging
from server.settings import CONFIG, LANGUAGE_CODE
from server.settings import LANGUAGES, LANGUAGES_KEYS
from database.models import User, UserProfile
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


@login_required
def index(request):
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
@login_required
def settings_view(request):
    if not request.user.has_perm("database.can_change_settings"):
        logger.debug(f'User "{request.user}" tried to access settings but does not have the neccessary permissions.')
        return redirect("index")
    settings_dict = {
        'Django': {
            'secret_key': {
                'section_name': _('frontend.settings.django'),
                'item_name': _('frontend.settings.secret_key'),
                'value': CONFIG.get('Django', 'secret_key'),
                'type': 'pass'
            },
            'debug': {
                'section_name': _('frontend.settings.django'),
                'item_name': _('frontend.settings.debug'),
                'value': CONFIG.get('Django', 'debug'),
                'type': 'bool'
            },
            'tz': {
                'section_name': _('frontend.settings.django'),
                'item_name': _('frontend.settings.tz'),
                'value': CONFIG.get('Django', 'tz'),
                'type': 'choice',
                'choices': [{'key': tzs, 'value': tzs } for tzs in pytz.common_timezones]
            }
        },
        'Networking': {
            'allowed_hosts': {
                'section_name': _('frontend.settings.networking'),
                'item_name': _('frontend.settings.allowed_hosts'),
                'value': CONFIG.get('Networking', 'allowed_hosts'),
                'type': 'list'
            },
            'csrf_trusted_origins': {
                'section_name': _('frontend.settings.networking'),
                'item_name': _('frontend.settings.csrf_trusted_origins'),
                'value': CONFIG.get('Networking', 'csrf_trusted_origins'),
                'type': 'list'
            }
        },
        'Other': {
            'instance_name': {
                'section_name': _('frontend.settings.other'),
                'item_name': _('frontend.settings.instance_name'),
                'value': CONFIG.get('Other', 'instance_name'),
                'type': 'str'
            }
        },
        'Localization': {
            'locale': {
                'section_name': _('frontend.settings.localization'),
                'item_name': _('frontend.settings.locale'),
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

@permission_required("database.can_invite")
@superuser_or_staff_required
def create_register_token(request):
    RegisterToken().save()
    return redirect('manager_user_list')

from plugins.functions import get_plugins

@permission_required("database.can_search")
def manga_search(request):
    return custom_render(request, "manga/search.html", {"plugins": get_plugins()})

from database.models import MangaRequest

@permission_required("database.can_manage_requests")
def manga_requests(request):
    return custom_render(request, "manga/requests.html", {"manga_requests": [{"plugin": r.plugin, "manga": r.variables, "pk": r.pk} for r in MangaRequest.objects.all()]})