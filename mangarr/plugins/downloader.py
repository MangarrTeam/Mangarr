import os
import tempfile
import shutil
import zipfile
import requests
from server.settings import PLUGINS_DIR
from .manager import update_downloaded_metadata

GITHUB_ZIP_URL = "https://github.com/{repo}/archive/refs/heads/{branch}.zip"

def download_plugin(repo, category, domain, version, branch="main"):
    url = GITHUB_ZIP_URL.format(repo=repo, branch=branch)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "plugin.zip")

        # Download ZIP
        r = requests.get(url)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            f.write(r.content)

        # Unzip it
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        # The zip will extract into a folder like REPO-main/
        root_folder = next((f for f in os.listdir(tmpdir) if os.path.isdir(os.path.join(tmpdir, f))), None)
        if not root_folder:
            raise Exception("Invalid ZIP structure")

        extracted_path = os.path.join(tmpdir, root_folder)

        # Determine path: core/DOMAIN or community/DOMAIN
        expected_subfolder = os.path.join(extracted_path, category, domain)
        if not os.path.exists(expected_subfolder):
            raise Exception(f"Expected plugin path not found: {expected_subfolder}")

        # Copy to correct destination
        dest_dir = os.path.join(PLUGINS_DIR, category, domain)
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.copytree(expected_subfolder, dest_dir)

        # Also copy manifest.json (should be at root of repo)
        manifest_src = os.path.join(extracted_path, "manifest.json")
        if os.path.exists(manifest_src):
            shutil.copy2(manifest_src, os.path.join(dest_dir, "manifest.json"))
        
        update_downloaded_metadata(domain, version)