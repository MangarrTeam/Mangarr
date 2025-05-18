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

LOCALE_PATH = Path(os.path.join(BASE_DIR, 'locale'))
LOCALE_PATH.mkdir(exist_ok=True)

LOCALE_PATHS = [
    LOCALE_PATH,
]