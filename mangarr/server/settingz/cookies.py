from .config import INSTANCE_NAME as _INSTANCE_NAME
from server.functions import sanitize_ascii

SESSION_COOKIE_NAME = sanitize_ascii(f'{_INSTANCE_NAME[:4000].lower()}_sessionid')
CSRF_COOKIE_NAME = sanitize_ascii(f'{_INSTANCE_NAME[:4000].lower()}_csrftoken')
LANGUAGE_COOKIE_NAME = sanitize_ascii(f'{_INSTANCE_NAME[:4000].lower()}_language')