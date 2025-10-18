from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import pgettext
from database.manga.models import Library

# Create your models here.
class PermissionCodename:
    def __init__(self, codename):
        self.codename = codename

    def __str__(self):
        return self.codename

    @property
    def name(self):
        return pgettext(
            f"Permission value for '{self.codename.replace('_', ' ').capitalize()}'",
            f"permission.{self.codename}"
        )


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    token = models.CharField(max_length=64, unique=True)
    allowed_libraries = models.ManyToManyField(Library, related_name='allowed_users')
    nsfw_allowed = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ('can_restart', pgettext("Permission value for 'Can restart'", 'permission.can_restart')),
            ('can_change_settings', pgettext("Permission value for 'Can change settings'", 'permission.can_change_settings')),
            ('can_invite', pgettext("Permission value for 'Can invite'", 'permission.can_invite')),
            ('can_manage_plugins', pgettext("Permission value for 'Can manage plugins'", 'permission.can_manage_plugins')),
            ('can_search', pgettext("Permission value for 'Can search'", 'permission.can_search')),
            ('can_request', pgettext("Permission value for 'Can request'", 'permission.can_request')),
            ('can_manage_requests', pgettext("Permission value for 'Can manage requests'", 'permission.can_manage_requests')),
            ('can_download', pgettext("Permission value for 'Can download'", 'permission.can_download')),
            ('can_manage_monitors', pgettext("Permission value for 'Can manage monitors'", 'permission.can_manage_monitors')),
            ('can_manage_metadata', pgettext("Permission value for 'Can manage metadata'", 'permission.can_manage_metadata')),
            ('can_manage_libraries', pgettext("Permission value for 'Can manage libraries'", 'permission.can_manage_libraries')),
            ('can_manage_connectors', pgettext("Permission value for 'Can manage connectors'", 'permission.can_manage_connectors')),
        ]

    def __str__(self) -> str:
        return f'{self.user.username} Profile'
    
    def get_custom_permissions(self) -> list:
        return [permission[0] for permission in self._meta.permissions]
    
    def regenerate_token(self) -> str:
        from core.utils import generate_unique_token
        self.token = generate_unique_token(UserProfile)
        self.save()
        return self.token

class RegisterToken(models.Model):
    token = models.CharField(max_length=64, unique=True, editable=False)

    def __str__(self) -> str:
        return self.token
    
    def regenerate_token(self) -> None:
        from core.utils import generate_unique_token
        self.token = generate_unique_token(RegisterToken)
        self.save()

    def save(self):
        from core.utils import generate_unique_token
        self.token = generate_unique_token(RegisterToken)
        super().save()