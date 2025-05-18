import threading
from plugins.tasks import background_update

threading.Thread(target=background_update, daemon=True).start()
