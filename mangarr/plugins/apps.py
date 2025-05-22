from django.apps import AppConfig
import threading
import signal


class PluginsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins'
    threads_started = False

    def ready(self):
        if not self.threads_started:
            from . import tasks
            tasks.stop_event = threading.Event()

            thread1 = threading.Thread(target=tasks.load_downloaded_plugins, daemon=True)
            thread2 = threading.Thread(target=tasks.background_update, daemon=True)

            def handle_sigterm(*args):
                tasks.stop_event.set()

            signal.signal(signal.SIGTERM, handle_sigterm)
            signal.signal(signal.SIGINT, handle_sigterm)

            thread1.start()
            thread2.start()

            self.threads_started = True
