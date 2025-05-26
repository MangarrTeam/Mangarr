from django.db import models
from django.utils.translation import pgettext
from database.manga.models import Manga, Volume, Chapter
from plugins.base import MangaPluginBase
from plugins.functions import get_plugin_by_key
from server.settings import FILE_PATH_ROOT, CACHE_FILE_PATH_ROOT
import hashlib
import shutil
import zipfile
import time
import os
from django.utils import timezone
from datetime import timedelta
import datetime
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from database.manga.functions import make_valid_filename
from .functions import convert_datetime, move_file
from django.db.models import Q
import logging
logger = logging.getLogger(__name__)



def make_json_serializable(value):
    if isinstance(value, dict):
        return {k: make_json_serializable(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [make_json_serializable(v) for v in value]
    elif isinstance(value, datetime.datetime):
        return value.isoformat()
    elif isinstance(value, datetime.date):
        return value.isoformat()
    elif isinstance(value, datetime.time):
        return value.isoformat()
    return value

# Create your models here.
class ProcessBase(models.Model):
    plugin = models.CharField(verbose_name=pgettext("Plugin field name", "processes.models.process_base.plugin"))
    url = models.URLField(verbose_name=pgettext("URL field name", "processes.models.process_base.url"), unique=True)
    last_run = models.DateTimeField(blank=True, null=True, verbose_name=pgettext("Last run field name", "processes.models.process_base.last_run"))
    arguments = models.JSONField(default=dict, verbose_name=pgettext("Arguments JSON field name", "processes.models.process_base.arguments"), blank=True)
    
    class Meta:
        abstract = True

    def get_plugin(self) -> MangaPluginBase:
        return get_plugin_by_key(self.plugin)

    def __str__(self):
        return f'{self.arguments.get("name") or super().__str__()} ({self.plugin})'
    
    def save(self, *args, **kwargs):
        self.arguments = make_json_serializable(self.arguments)
        super().save(*args, **kwargs)


class MangaAlreadyExist(Exception):
    pass

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
     
class MonitorManga(ProcessBase):
    def update(self):
        try:
            plugin = self.get_plugin()
            manga_data = plugin.get_manga(self.arguments)

            manga, manga_created = Manga.objects.get_or_create(url=manga_data.get("url"))

            if manga_created:
                manga.choose_plugin(self.plugin)


            manga.update_fields({
                **self.arguments,
                **manga_data
            })

            seen_urls = set()
            unique_chapters = []

            for ch_data in sorted(plugin.get_chapters(manga_data), key=lambda x: (float(x.get("volume_number")), float(x.get("chapter_number")))):
                url = ch_data.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                unique_chapters.append(ch_data)

            # Step 2: Get existing MonitorChapter URLs from DB
            existing_urls = set(
                MonitorChapter.objects
                .filter(url__in=seen_urls, manga=manga)
                .values_list("url", flat=True)
            )

            # Step 3: Filter out existing and prepare new instances
            new_chapters = []

            for ch_data in unique_chapters:
                url = ch_data["url"]
                if url in existing_urls:
                    continue

                chapter = MonitorChapter(
                    url=url,
                    manga=manga,
                    plugin=self.plugin,
                    arguments=convert_datetime(ch_data)
                )
                new_chapters.append(chapter)


            MonitorChapter.objects.bulk_create(new_chapters, batch_size=100)

            self.delete()
        except Exception as e:
            self.last_run = timezone.now()
            self.save()
            logger.error(f"Error - {e}")

class PageWasNone(Exception):
    pass
   
class MonitorChapter(ProcessBase):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, verbose_name=pgettext("Manga FK name", "processes.models.monitor_chapter.manga"))
    def update(self):
        try:
            plugin = self.get_plugin()
            chapter_data = self.arguments

            volume_number = float(chapter_data.get("volume_number", 1.0))
            volume = None
            for v in Volume.objects.filter(manga=self.manga):
                if v.number.value == volume_number:
                    volume = v
                    break

            if volume is None:
                volume = Volume.objects.create(manga=self.manga)
                volume.number.value = volume_number

            chapter, created = Chapter.objects.get_or_create(url=chapter_data.get("url"), volume=volume)
            
            chapter.update_fields({
                **self.arguments,
                **chapter_data
            })

            if chapter.downloaded:
                logger.debug(f"Chapter '{chapter.name.value}' already downloaded, skipping...")
                self.delete()
                time.sleep(10)
                return

            chapter_cache_folder = f'{self.plugin} {self.manga.name.value} {self.url}'
            chapter_cache_file_path_name = CACHE_FILE_PATH_ROOT / f"{get_hash(chapter_cache_folder)}.cbz"

            chapter_pages = plugin.get_pages(self.arguments)

            with zipfile.ZipFile(chapter_cache_file_path_name, 'w', zipfile.ZIP_DEFLATED) as cbz:
                width = len(str(len(chapter_pages)))
                for i, page in enumerate(chapter_pages):
                    page_stream = plugin.download_page(page['url'], page.get('arguments', {}))
                    if page_stream is None:
                        raise PageWasNone(f"Page {i} was None, skipping chapter will retry later")
                    filename = f"{i+1:0{width}}.png"
                    cbz.writestr(filename, page_stream.getvalue())
                    on_download(i+1, len(chapter_pages))
                    # Delay for 1 second between downloads
                    time.sleep(0.5)

                cbz.writestr("ComicInfo.xml", chapter.create_xml())
            on_download(0, 0)

            chapter_file_folder = FILE_PATH_ROOT / f"{make_valid_filename(chapter.volume.manga.name.value)}"
            chapter_file_folder.mkdir(exist_ok=True)
            chapter_file_path_name = chapter_file_folder / chapter.get_file_name()

            try:
                move_file(chapter_cache_file_path_name, chapter_file_path_name)
                chapter.file = f"{chapter_file_path_name}"
                chapter.downloaded = True
                chapter.save()
            except Exception as e:
                logger.error(f"Error - {e}")

            self.delete()

            # Delay for 10 seconds
            time.sleep(10)

        except Exception as e:
            self.last_run = timezone.now()
            self.save()
            logger.error(f"Error - {e}")

from websockets.consumers import notify_clients

@receiver(post_save, sender=MonitorManga)
@receiver(post_delete, sender=MonitorManga)
@receiver(post_save, sender=MonitorChapter)
@receiver(post_delete, sender=MonitorChapter)
def monitor_changed(sender, instance, **kwargs):
    one_hour_ago = timezone.now() - timedelta(hours=1)
    data = {
        "scanning": {
            "manga": len(MonitorManga.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True))),
            "chapters": len(MonitorChapter.objects.filter(Q(last_run__lt=one_hour_ago) | Q(last_run__isnull=True)))
        },
    }
    notify_clients(data)

def on_download(current:int, of:int):
    data = {
        "downloading": {
            "current": current,
            "of": of
        }
    }
    notify_clients(data)