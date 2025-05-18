import os, requests
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

def fetch_json_list(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f'Failed to fetch list: {url} - {e}')
        return []