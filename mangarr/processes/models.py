from django.db import models
from django.utils.translation import gettext_lazy as _
from database.manga.models import Manga, Volume, Chapter
from plugins.base import MangaPluginBase
from plugins.functions import get_plugin_by_key
from server.settings import FILE_PATH_ROOT, CACHE_FILE_PATH_ROOT
import hashlib
import shutil
import zipfile
import os
from django.utils import timezone
import datetime
from database.manga.functions import make_valid_filename
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
    plugin = models.CharField(verbose_name=_("processes.models.process_base.plugin"))
    url = models.URLField(verbose_name=_("processes.models.process_base.url"), unique=True)
    last_run = models.DateTimeField(blank=True, null=True, verbose_name=_("processes.models.process_base.last_run"))
    arguments = models.JSONField(default=dict, verbose_name=_("processes.models.process_base.arguments"), blank=True)
    
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

            manga, created = Manga.objects.get_or_create(url=manga_data.get("url"))

            manga.update_fields({
                **self.arguments,
                **manga_data
            })

            for found_chapter in plugin.get_chapters(manga_data):
                url = found_chapter.get("url")
                if url is None:
                    continue
                monitor_chapter, created = MonitorChapter.objects.get_or_create(url=url, manga=manga)
                if not created:
                    continue
                monitor_chapter.plugin = self.plugin
                monitor_chapter.arguments = found_chapter
                monitor_chapter.save()

            self.delete()
        except Exception as e:
            self.last_run = timezone.now()
            self.save()
            logger.error(f"Error - {e}")
   
class MonitorChapter(ProcessBase):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, verbose_name=_("processes.models.monitor_chapter.manga"))
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

            chapter_cache_folder = f'{self.plugin} {self.manga.name.value} {self.url}'
            chapter_cache_file_path_name = CACHE_FILE_PATH_ROOT / f"{get_hash(chapter_cache_folder)}.cbz"

            chapter_pages = plugin.get_pages(self.arguments)

            with zipfile.ZipFile(chapter_cache_file_path_name, 'w', zipfile.ZIP_DEFLATED) as cbz:
                width = len(str(len(chapter_pages)))
                for i, page in enumerate(chapter_pages):
                    page_stream = plugin.download_page(page['url'], page.get('arguments', {}))
                    filename = f"{i+1:0{width}}.png"
                    cbz.writestr(filename, page_stream.getvalue())

                cbz.writestr("ComicInfo.xml", chapter.create_xml())

            chapter_file_folder = FILE_PATH_ROOT / f"{make_valid_filename(chapter.volume.manga.name.value)}"
            chapter_file_folder.mkdir(exist_ok=True)
            chapter_file_path_name = chapter_file_folder / chapter.get_file_name()

            shutil.move(chapter_cache_file_path_name, chapter_file_path_name)
            chapter.file = f"{chapter_file_path_name}"
            chapter.downloaded = True
            chapter.save()
            self.delete()

        except Exception as e:
            self.last_run = timezone.now()
            self.save()
            logger.error(f"Error - {e}")