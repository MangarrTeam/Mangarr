import time
from django.utils import timezone
from datetime import timedelta
import threading
import os
import shutil
from server.settings import CACHE_FILE_PATH_ROOT

from .models import MonitorManga, MonitorChapter, Manga

import logging
logger = logging.getLogger(__name__)


monitoring_trigger = threading.Event()

def trigger_monitor():
    monitoring_trigger.set()

def clear_cache():
    logger.debug("Clearing cache folder")
    for filename in os.listdir(CACHE_FILE_PATH_ROOT):
        file_path = os.path.join(CACHE_FILE_PATH_ROOT, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    logger.debug("Cache folder cleared")

def monitoring():
    while True:
        logger.debug("Monitoring check...")
        clear_cache()
        threshold = timezone.now() - timedelta(hours=24)

        for manga in Manga.objects.filter(last_update__lt=threshold):
            try:
                manga = MonitorManga.objects.get_or_create(plugin=manga.plugin, url=manga.url, arguments=manga.arguments)
            except Manga.DoesNotExist as e:
                logger.warning(f"Manga missing - {e}")
            except Exception as e:
                logger.error(f"Error - {e}")

        for manga_monitor in MonitorManga.objects.all():
            try:
                manga_monitor.update()
            except MonitorManga.DoesNotExist as e:
                logger.warning(f"Manga monitor missing - {e}")
            except Exception as e:
                logger.error(f"Error - {e}")
        
        for chapter_monitor in MonitorChapter.objects.all():
            try:
                chapter_monitor.update()
            except MonitorChapter.DoesNotExist as e:
                logger.warning(f"Chapter monitor missing - {e}")
            except Exception as e:
                logger.error(f"Error - {e}")

        triggered = monitoring_trigger.wait(3600)
        if triggered:
            monitoring_trigger.clear()

        #time.sleep(3600)