from django.db.utils import OperationalError
from django.db.models import Q
import time
from django.utils import timezone
from datetime import timedelta
import os
import shutil
from core.settings import CACHE_FILE_PATH_ROOT
from connectors.utils import notify_connectors
from database.manga.models import Library
from datetime import datetime, timedelta
from core.thread_manager import stop_event

from .models import MonitorManga, MonitorChapter, Manga, ChapterDownloaded, ChapterHadNoPages, EditChapter

import logging
logger = logging.getLogger(__name__)

def clear_cache():
    logger.debug("Clearing cache folder")
    for filename in os.listdir(CACHE_FILE_PATH_ROOT):
        file_path = os.path.join(CACHE_FILE_PATH_ROOT, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    logger.debug("Cache folder cleared")

def process_exists() -> bool:
    one_hour_ago = timezone.now() - timedelta(hours=1)
    threshold = timezone.now() - timedelta(hours=24)
    return Manga.objects.filter(last_update__lt=threshold).exists() or MonitorChapter.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)).exists() or MonitorManga.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)).exists() or EditChapter.objects.all().exists()

def update_updates(updates:set, library:Library, modified:bool):
    if library not in updates and modified:
        updates.add(library)

next_run = None
def monitoring():
    global next_run
    while not stop_event.is_set():
        if next_run is None or next_run <= timezone.now():
            updated = False
            updates = set()
            try:
                while process_exists() and not stop_event.is_set():
                    logger.debug("Monitoring check...")
                    clear_cache()
                    one_hour_ago = timezone.now() - timedelta(hours=1)
                    threshold = timezone.now() - timedelta(hours=24)
            
                    for manga in Manga.objects.filter(last_update__lt=threshold):
                        if stop_event.is_set():
                            return
                        try:
                            monitor_manga, monitor_created = MonitorManga.objects.get_or_create(library=manga.library, plugin=manga.plugin, url=manga.url, arguments=manga.arguments, manga=manga)
                            update_updates(updates, monitor_manga.library, monitor_created)
                        except Manga.DoesNotExist as e:
                            logger.warning(f"Manga missing - {e}")
                        except Exception as e:
                            logger.error(f"Error - {e}")

                    if stop_event.is_set():
                        return

                    for manga_monitor in MonitorManga.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)):
                        if stop_event.is_set():
                            return
                        try:
                            manga_monitor.update()
                            update_updates(updates, manga_monitor.library, True)
                        except MonitorManga.DoesNotExist as e:
                            logger.warning(f"Manga monitor missing - {e}")
                        except Exception as e:
                            logger.error(f"Error - {e}")
                    
                    if stop_event.is_set():
                        return

                    skipped_chapters = []
                    for chapter_monitor in MonitorChapter.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)):
                        if stop_event.is_set():
                            return
                        try:
                            chapter_monitor.update()
                            update_updates(updates, chapter_monitor.manga.library, True)
                        except ChapterDownloaded:
                            logger.debug(f"Chapter already downloaded, skipping...")
                            skipped_chapters.append(chapter_monitor.pk)
                        except ChapterHadNoPages:
                            logger.debug(f"Chapter had no pages, will try again later...")
                            skipped_chapters.append(chapter_monitor.pk)
                        except MonitorChapter.DoesNotExist as e:
                            logger.warning(f"Chapter monitor missing - {e}")
                        except Exception as e:
                            logger.error(f"Error - {e}")

                    MonitorChapter.objects.filter(pk__in=skipped_chapters).delete()
                    
                    if stop_event.is_set():
                        return

                    for editChapter in EditChapter.objects.all():
                        if stop_event.is_set():
                            return
                        try:
                            library = editChapter.chapter.volume.manga.library
                            editChapter.update()
                            update_updates(updates, library, True)
                        except Exception as e:
                            logger.error(f"Error - {e}")
                    
                    if stop_event.is_set():
                        return

                if len(updates) != 0:
                    for lib in updates:
                        notify_connectors(lib)
                    
                if stop_event.is_set():
                    return



            except OperationalError as e:
                logger.error(f"Error - {e}")

            next_run = timezone.now() + timedelta(hours=1)
        time.sleep(10)  # 10 seconds

def trigger_monitor():
    global next_run
    next_run = None