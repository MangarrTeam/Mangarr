from django.apps import AppConfig


class ProcessesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'processes'
    threads_started = False

    def ready(self):
        if not self.threads_started:
            import processes.signals
            self.threads_started = True