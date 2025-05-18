import pathlib
import os
from django.conf import settings
import secrets
import logging
from django.db import models
from django.contrib.auth.decorators import user_passes_test


logger = logging.getLogger(__name__)

def restart_app() -> None:
    pathlib.Path(os.path.join(settings.BASE_DIR, "server", "settings.py")).touch()
    logger.info("Restart triggered")

def generate_unique_token(model:models.Model):
    while True:
        token = secrets.token_hex(32)
        if not model.objects.filter(token=token).exists():
            return token

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)

def superuser_or_staff_required(view_func):
    return user_passes_test(lambda u: u.is_superuser or u.is_staff)(view_func)
