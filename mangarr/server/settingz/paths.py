from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = Path(os.path.join(BASE_DIR, 'project_root'))
PROJECT_ROOT.mkdir(exist_ok=True)

LOG_DIR = Path(os.path.join(PROJECT_ROOT, 'logs'))
LOG_DIR.mkdir(exist_ok=True)

CONFIG_DIR = Path(os.path.join(PROJECT_ROOT, 'config'))
CONFIG_DIR.mkdir(exist_ok=True)
CONFIG_PATH = Path(os.path.join(CONFIG_DIR, 'mangarr.conf'))

DATABASE_DIR = Path(os.path.join(PROJECT_ROOT, 'database'))
DATABASE_DIR.mkdir(exist_ok=True)

PLUGINS_DIR = Path(os.path.join(PROJECT_ROOT, 'plugins'))
PLUGINS_DIR.mkdir(exist_ok=True)
CORE_PLUGINS_DIR = Path(os.path.join(PLUGINS_DIR, 'core'))
CORE_PLUGINS_DIR.mkdir(exist_ok=True)
COMMUNITY_PLUGINS_DIR = Path(os.path.join(PLUGINS_DIR, 'community'))
COMMUNITY_PLUGINS_DIR.mkdir(exist_ok=True)
PLUGINS_CACHE_DIR = Path(os.path.join(PLUGINS_DIR, 'cache'))
PLUGINS_CACHE_DIR.mkdir(exist_ok=True)
PLUGINS_METADATA_PATH = Path(os.path.join(PLUGINS_DIR, 'plugins_metadata.json'))

LOCALE_PATH = Path(os.path.join(BASE_DIR, 'locale'))
LOCALE_PATH.mkdir(exist_ok=True)

LOCALE_PATHS = [
    LOCALE_PATH,
]