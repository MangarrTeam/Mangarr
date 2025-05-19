import threading
from plugins.tasks import background_update, load_downloaded_plugins

threading.Thread(target=load_downloaded_plugins, daemon=True).start()
threading.Thread(target=background_update, daemon=True).start()
