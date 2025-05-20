from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from plugins.utils import get_downloaded_metadata

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    token = models.CharField(max_length=64, unique=True)

    class Meta:
        permissions = [
            ('can_restart', _('permission.can_restart')),
            ('can_change_settings', _('permission.can_change_settings')),
            ('can_invite', _('permission.can_invite')),
            ('can_manage_plugins', _('permission.can_manage_plugins')),
            ('can_search', _('permission.can_search')),
            ('can_request', _('permission.can_request')),
            ('can_manage_requests', _('permission.can_manage_requests')),
            ('can_download', _('permission.can_download')),
        ]


    def __str__(self) -> str:
        return f'{self.user.username} Profile'
    
    def get_custom_permissions(self) -> list:
        return [permission[0] for permission in self._meta.permissions]
    
    def regenerate_token(self) -> None:
        from server.functions import generate_unique_token
        self.token = generate_unique_token(UserProfile)
        self.save()

class RegisterToken(models.Model):
    token = models.CharField(max_length=64, unique=True, editable=False)

    def __str__(self) -> str:
        return self.token
    
    def regenerate_token(self) -> None:
        from server.functions import generate_unique_token
        self.token = generate_unique_token(RegisterToken)
        self.save()

    def save(self):
        from server.functions import generate_unique_token
        self.token = generate_unique_token(RegisterToken)
        super().save()


def get_choices() -> list[tuple]:
    return [
        (f'{pm["category"]}_{pm["domain"]}', f'{pm["name"]} ({pm["category"]})')
        for pm in get_downloaded_metadata()
        if pm.get("category") and pm.get("domain") and pm.get("name")
    ]

class MangaRequest(models.Model):
    plugin = models.CharField(max_length=64, choices=get_choices(), verbose_name=_("database.models.manga_request.plugin"))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("database.models.manga_request.requested_by"))
    variables = models.JSONField(default=dict, blank=True, verbose_name=_("database.models.manga_request.variables"))


    @staticmethod
    def has_plugin(category:str, domain:str) -> bool:
        return any([ch[0] == f'{category}_{domain}' for ch in get_choices()])
    

    def choose_plugin(self, category:str, domain:str) -> None:
        choices = get_choices()
        if not any([ch[0] == f'{category}_{domain}' for ch in choices]):
            return
        
        for choice in choices:
            if choice[0] == f'{category}_{domain}':
                self.plugin = choice[0]

    @staticmethod
    def request_exist(url:str) -> bool:
        for req in MangaRequest.objects.filter(variables__has_key="url"):
            req_url = req.variables.get("url")
            if req_url is not None and req_url == url:
                return True
        return False
    
    def save(self):
        if self.variables.get("url") is None:
            raise Exception("The variables need at least 'url'")

        super().save()

    def __str__(self):
        return f'{self.variables["name"] if self.variables.get("name") else self.get("url")} ({self.get_plugin_display()})'