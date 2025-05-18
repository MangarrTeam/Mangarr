import json
from server.settings import PLUGINS_METADATA_PATH

def load_metadata():
    with open(PLUGINS_METADATA_PATH) as f:
        return json.load(f)