import pathlib
import subprocess
import os
from django.conf import settings
import secrets
import logging
from django.db import models
from django.contrib.auth.decorators import user_passes_test
import re

logger = logging.getLogger(__name__)

def restart_app() -> None:
    try:
        subprocess.run(["supervisorctl", "restart", "gunicorn", "redis", "daphne"], check=True)
        logger.info("Gunicorn restart triggered via supervisorctl")
    except subprocess.CalledProcessError as e:
        logger.error("Failed to restart Gunicorn: %s", e)

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

def sanitize_ascii(input_string: str) -> str:
    sanitized = input_string.replace(' ', '_')
    sanitized = ''.join(c if ord(c) < 128 else '_' for c in sanitized)
    sanitized = re.sub(r'[^A-Za-z0-9_-]', '_', sanitized)
    return sanitized