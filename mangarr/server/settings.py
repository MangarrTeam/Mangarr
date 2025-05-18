from pathlib import Path
import os


from .settingz.flags import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from .settingz.paths import *

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = LOGIN_URL

# Configs
from .settingz.config import *

# CSRF
from .settingz.csrf import *

# Application definition
from .settingz.installed_apps import *


# Database
from .settingz.database import *


# Password validation
from .settingz.auth_validators import *


# Internationalization
from .settingz.localization import *


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


MEDIA_ROOT = os.environ.get('IMAGES_DIR', '/uploads/')
MEDIA_URL = '/uploads/'

LOG_DIR = Path(os.path.join(PROJECT_ROOT, 'logs'))
LOG_DIR.mkdir(exist_ok=True)

# Logging setting
from .settingz.logging import *


