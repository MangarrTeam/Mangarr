import threading
from processes.tasks import monitoring

threading.Thread(target=monitoring, daemon=True).start()
