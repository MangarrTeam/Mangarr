from django.apps import AppConfig


class PluginsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins'
    threads_started = False

    def ready(self):
        if not self.threads_started:
            import plugins.signals
            self.threads_started = True
