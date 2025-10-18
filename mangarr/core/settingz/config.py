from . import paths
from ..config import SmartConfig
from .localization import LANGUAGES_KEYS

CONFIG:SmartConfig = SmartConfig(paths.CONFIG_PATH)

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


SECRET_KEY = CONFIG.get('Django', 'secret_key', 'your-secret-key', description='Secret key to Django (change this to something unique)')

DEBUG = CONFIG.getboolean('Django', 'debug', fallback=False, description='Enables DEBUG logging')

ALLOWED_HOSTS = CONFIG.get('Networking', 'allowed_hosts', '*', description='List of allowed hosts separated by comma (",")').split(',')

TIME_ZONE = CONFIG.get('Django', 'tz', 'UTC', description='Django Timezone')

INSTANCE_NAME = CONFIG.get('Other', 'instance_name', 'Mangarr', description='Name of this instance. Displayed in tab.')

LANGUAGE_CODE = CONFIG.get('Localization', 'locale', 'en', description='Default language.', choices=LANGUAGES_KEYS)