import os, json
from plugins.plugin_sources import SOURCE_LISTS
from plugins.utils import fetch_repo_manifest, fetch_json_list
import logging
from server.settings import PLUGINS_DIR, PLUGINS_METADATA_PATH
from packaging.version import Version
from django.core.cache import cache

logger = logging.getLogger(__name__)

def update_metadata():
    plugin_data = []

    known_keys = set()

    for category, source_url in SOURCE_LISTS.items():
        repos = fetch_json_list(source_url)
        for repo in repos:
            manifest = fetch_repo_manifest(repo)
            if manifest:
                key = f"{category}:{manifest['domain']}"
                known_keys.add(key)
                version = Version(manifest["version"])
                downloaded = get_downloaded_version(category, manifest["domain"])
                downloaded_version = f"{Version(downloaded)}" if downloaded is not None else downloaded
                plugin_data.append({
                    **manifest,
                    "version": f'{version}',
                    "source": repo,
                    "category": category,
                    "downloaded_version": downloaded_version,
                    "has_update": (downloaded is not None and version > Version(downloaded)),
                    "local_only": False,
                })

    for category_dir in PLUGINS_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        category = category_dir.name

        for domain_dir in category_dir.iterdir():
            if not domain_dir.is_dir():
                continue
            domain = domain_dir.name
            key = f"{category}:{domain}"

            if key in known_keys:
                continue

            try:
                manifest = get_downloaded_manifest(category, domain) or {}
                version = manifest.get("version", "0.0.0")

                plugin_data.append({
                    "domain": domain,
                    "name": manifest.get("name", domain),
                    "codeowner": manifest.get("codeowner", []),
                    "documentation": manifest.get("documentation"),
                    "issue_tracker": manifest.get("issue_tracker"),
                    "version": version,
                    "source": None,
                    "category": category,
                    "downloaded_version": version,
                    "has_update": False,
                    "local_only": True,
                })
            except Exception as e:
                logger.warning(f"Could not load local plugin {category}/{domain}: {e}")

    with open(PLUGINS_METADATA_PATH, "w") as f:
        json.dump(plugin_data, f, indent=2)

def update_downloaded_metadata(domain, version=None):
    try:
        with open(PLUGINS_METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except FileNotFoundError as e:
        logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
        metadata = []
    except Exception as e:
        logger.error(f'Error while reading {PLUGINS_METADATA_PATH} - {e}')
        metadata = []

    updated = False
    for plugin in metadata:
        if plugin.get("domain") == domain:
            if version is not None:
                plugin["downloaded_version"] = f"{Version(version)}"
            else:
                plugin["downloaded_version"] = None
            plugin["has_update"] = False
            updated = True
            break
    
    if updated:
        with open(PLUGINS_METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    else:
        logger.error(f"Plugin domain '{domain}' not found in metadata cache.")


def get_downloaded_manifest(category, domain) -> dict:
    domain_path = os.path.join(PLUGINS_DIR, category, domain)
    if not os.path.isdir(domain_path):
        return None
    try:
        with open(os.path.join(domain_path, "manifest.json")) as f:
            return json.load(f)
    except:
        return None
    
def get_downloaded_version(category, domain):
    manifest = get_downloaded_manifest(category, domain)
    return manifest.get("version") if manifest else None

from .base import MangaPluginBase
def get_plugin(category, domain) -> MangaPluginBase:
    cache.get(f'{category}.{domain}')