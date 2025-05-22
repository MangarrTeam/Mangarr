from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

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