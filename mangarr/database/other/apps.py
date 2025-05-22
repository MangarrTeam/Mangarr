from django.apps import AppConfig
from django.utils.translation import gettext as _
import re


class OtherConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'database.other'
    label = 'database_other'

    def ready(self):
        from django.contrib.auth.models import Permission

        def custom_str(self):
            # self.name is e.g. "permission.can_restart"
            pretty_model = re.sub(r'(?<!^)(?=[A-Z])', ' ', self.content_type.model_class().__name__)
            # gettext will look that key up in your .po/.mo files
            return f"{self.content_type.app_label} | {pretty_model} | {_(self.name)}"

        Permission.__str__ = custom_str
