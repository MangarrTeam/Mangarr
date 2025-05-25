from django.db.utils import OperationalError
from django.db.models import Q
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
stop_event = None

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

def monitoring_exists() -> bool:
    one_hour_ago = timezone.now() - timedelta(hours=1)
    return MonitorChapter.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)).exists() or MonitorManga.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)).exists()

def monitoring():
    while not stop_event.is_set():
        try:
            while monitoring_exists():
                logger.debug("Monitoring check...")
                clear_cache()
                one_hour_ago = timezone.now() - timedelta(hours=1)
                threshold = timezone.now() - timedelta(hours=24)

                for manga in Manga.objects.filter(last_update__lt=threshold):
                    if stop_event.is_set():
                        break
                    try:
                        manga = MonitorManga.objects.get_or_create(plugin=manga.plugin, url=manga.url, arguments=manga.arguments)
                    except Manga.DoesNotExist as e:
                        logger.warning(f"Manga missing - {e}")
                    except Exception as e:
                        logger.error(f"Error - {e}")

                
                if stop_event.is_set():
                    break

                for manga_monitor in MonitorManga.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)):
                    if stop_event.is_set():
                        break
                    try:
                        manga_monitor.update()
                    except MonitorManga.DoesNotExist as e:
                        logger.warning(f"Manga monitor missing - {e}")
                    except Exception as e:
                        logger.error(f"Error - {e}")
                
                for chapter_monitor in MonitorChapter.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)):
                    if stop_event.is_set():
                        break
                    try:
                        chapter_monitor.update()
                    except MonitorChapter.DoesNotExist as e:
                        logger.warning(f"Chapter monitor missing - {e}")
                    except Exception as e:
                        logger.error(f"Error - {e}")
                
                if stop_event.is_set():
                    break
            
            if stop_event.is_set():
                break

            triggered = monitoring_trigger.wait(3600)

            if stop_event.is_set():
                break

            if triggered:
                monitoring_trigger.clear()
            
            
        except OperationalError as e:
            logger.debug(f"Error - {e}")
        #time.sleep(3600)