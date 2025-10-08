from django.conf import settings
import secrets, logging, re, hashlib, subprocess
from django.db import models
from django.contrib.auth.decorators import user_passes_test

logger = logging.getLogger(__name__)

def restart_app() -> None:
    try:
        subprocess.run(["python", "/app/restart_mangarr.py"], check=True)
        logger.info("Mangarr restart triggered via python")
    except subprocess.CalledProcessError as e:
        logger.error("Failed to restart Mangarr: %s", e)

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

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()