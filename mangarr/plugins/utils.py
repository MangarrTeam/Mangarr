import os, requests, json
from server.settings import PLUGINS_METADATA_PATH
import logging
logger = logging.getLogger(__name__)

def fetch_repo_manifest(repo):
    try:
        url = f"https://raw.githubusercontent.com/{repo}/main/manifest.json"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f'Failed to fetch manifest for {repo}: {e}')
        return None
    
def get_downloaded_metadata() -> list[dict]:
    with open(PLUGINS_METADATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except FileNotFoundError as e:
            logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
            return []
        except Exception as e:
            logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
            return []
    
def fetch_json_list(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f'Failed to fetch list: {url} - {e}')
        return []