from django.apps import AppConfig
import threading
import signal
import os

import logging
logger = logging.getLogger(__name__)

class ProcessesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'processes'
    threads_started = False

    def ready(self):
        if os.environ.get('RUN_THREADS', 'false') == 'true':
            return
        if not self.threads_started:
            from . import tasks
            tasks.stop_event = threading.Event()

            thread = threading.Thread(target=tasks.monitoring, daemon=True)

            def handle_sigterm(*args):
                tasks.stop_event.set()
                tasks.trigger_monitor()

            signal.signal(signal.SIGTERM, handle_sigterm)
            signal.signal(signal.SIGINT, handle_sigterm)

            thread.start()

            self.threads_started = True