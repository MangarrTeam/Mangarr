from django.apps import AppConfig
import threading
import signal
import os

import logging
logger = logging.getLogger(__name__)

class ProcessesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'processes'