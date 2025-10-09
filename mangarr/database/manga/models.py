from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import pgettext
from plugins.utils import get_plugin_choices, get_plugin_by_key
from plugins.base import MangaPluginBase, NO_THUMBNAIL_URL, Formats, AgeRating, Status
from .lockable_fields import LockableCharField, LockableListField, LockableBoolField, LockableIntegerField, LockableFloatField, LockableDateTimeField, LockableEnumField
from core.settings import FILE_PATH_ROOT
import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.sax.saxutils import unescape
from core.utils import get_hash
from django.utils import timezone
from .utils import make_valid_filename, BaseModel
from pathlib import Path
from datetime import datetime

# Create your models here.
class Library(BaseModel):
    name = models.CharField(max_length=64, default="Library", verbose_name=pgettext("Name field name for library", "database.models.library.name"), unique=True)
    folder = models.CharField(max_length=512, default=FILE_PATH_ROOT, verbose_name=pgettext("Folder field name for Library", "database.models.library.folder_path"))
    default = models.BooleanField(default=False, verbose_name=pgettext("Default field name for Library", "database.models.library.default"))

    def set_folder_path(self, name:str="") -> None:
        if len(name) == 0:
            name = self.name
        self.folder = FILE_PATH_ROOT / f"{make_valid_filename(name)}"
        self.folder.mkdir(exist_ok=True)

    @staticmethod
    def get_folders() -> list[str]:
        return [f.name for f in FILE_PATH_ROOT.iterdir() if f.is_dir()]

    def make_default(self):
        Library.objects.update(default=False)
        self.default = True
        self.save()

class MangaRequest(BaseModel):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, blank=False, null=False, verbose_name=pgettext("Library field name for Manga request", "database.models.manga_request.library"))
    plugin = models.CharField(max_length=64, choices=get_plugin_choices(), verbose_name=pgettext("Plugin field name for MangaRequest", "database.models.manga_request.plugin"))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=pgettext("User FK field name for MangaRequest", "database.models.manga_request.requested_by"))
    variables = models.JSONField(default=dict, blank=True, verbose_name=pgettext("Variables JSON field name for MangaRequest", "database.models.manga_request.variables"))

    @staticmethod
    def has_plugin(category:str, domain:str) -> bool:
        return any([ch[0] == f'{category}_{domain}' for ch in get_plugin_choices()])
    
    def get_plugin(self) -> MangaPluginBase:
        return get_plugin_by_key(self.plugin)    
    
    def get_plugin_name(self, key:str) -> str:
        choices = get_plugin_choices()
        if not any([ch[0] == key for ch in choices]):
            return key
        
        for choice in choices:
            if choice[0] == key:
                return choice[1]
        return key

    def choose_plugin(self, category:str, domain:str) -> None:
        choices = get_plugin_choices()
        if not any([ch[0] == f'{category}_{domain}' for ch in choices]):
            return
        
        for choice in choices:
            if choice[0] == f'{category}_{domain}':
                self.plugin = choice[0]

    @staticmethod
    def request_exist(url:str) -> bool:
        for req in MangaRequest.objects.filter(variables__has_key="url"):
            req_url = req.variables.get("url")
            if req_url is not None and req_url == url:
                return True
        return False

    @staticmethod
    def delete_if_exist(url:str):
        for req in MangaRequest.objects.filter(variables__has_key="url"):
            req_url = req.variables.get("url")
            if req_url is not None and req_url == url:
                req.delete()

    def save(self):
        if self.variables.get("url") is None:
            raise Exception("The variables need at least 'url'")

        super().save()

    def __str__(self):
        return f'{self.variables["name"] if self.variables.get("name") else self.get("url")} ({self.get_plugin_display()})'
    
class Manga(BaseModel):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, blank=False, null=False, verbose_name=pgettext("Library field name for Manga", "database.models.manga.library"))
    plugin = models.CharField(max_length=64, choices=get_plugin_choices(), verbose_name=pgettext("Plugin field name for Manga", "database.models.manga.plugin"))
    name = LockableCharField(verbose_name=pgettext("Name field name for Manga", "database.models.manga.name"))
    localized_name = LockableCharField(verbose_name=pgettext("Localized name field name for Manga", "database.models.manga.localized_name"))
    description = LockableCharField(verbose_name=pgettext("Description field name for Manga", "database.models.manga.description"))
    genres = LockableListField(verbose_name=pgettext("Genres field name for Manga", "database.models.manga.genres"))
    tags = LockableListField(verbose_name=pgettext("Tags field name for Manga", "database.models.manga.tags"))
    date_added = models.DateTimeField(auto_now_add=True, verbose_name=pgettext("Date added field name for Manga", "database.models.manga.date_added"))
    last_update = models.DateTimeField(auto_now_add=True, verbose_name=pgettext("Last update field name for Manga", "database.models.manga.last_update"))
    complete = LockableBoolField(verbose_name=pgettext("Complete field name for Manga", "database.models.manga.complete"))
    url = models.URLField(verbose_name=pgettext("URL field name for Manga", "database.models.manga.url"), unique=True)
    file_folder = models.CharField(max_length=512, default=FILE_PATH_ROOT, verbose_name=pgettext("Folder field name for Manga", "database.models.manga.folder_path"))
    arguments = models.JSONField(default=dict, verbose_name=pgettext("Arguments JSON field name for Manga", "processes.models.manga.arguments"), blank=True)

    def __str__(self) -> str:
        return self.name.value
    
    @property
    def cover(self) -> str:
        return self.arguments.get("cover", NO_THUMBNAIL_URL)
    
    @property
    def folder(self) -> str:
        return Path(self.library.folder) / self.file_folder
    
    @property
    def nsfw(self) -> bool:
        return get_plugin_by_key(self.plugin).nsfw_allowed

    @staticmethod
    def monitor_exist(url:str) -> bool:
        return Manga.objects.filter(url=url).exists()
    
    def set_file_folder_path(self, name:str="") -> None:
        if len(name) == 0:
            name = get_hash(self.url)

        self.file_folder = f"{make_valid_filename(name)}"

    def choose_plugin(self, key:str) -> None:
        if self.plugin is not None and len(self.plugin) > 0:
            return
        choices = get_plugin_choices()
        if not any([ch[0] == key for ch in choices]):
            return
        
        for choice in choices:
            if choice[0] == key:
                self.plugin = choice[0]
    
    def add_alternative_names(self, alternative_names:list):
        for alternative_name in alternative_names:
            alt_name = MangaANLink()
            alt_name.manga = self
            alt_name.alternative_name.value = alternative_name
            alt_name.save()

    def update_last_update(self) -> None:
        self.last_update = timezone.now()
        self.save()

    def update_fields(self, data:dict, force:bool = False) -> None:
        if data.get("name") is not None:
            self.name.set_value(data.get("name"), force)

        if data.get("name_lock") is not None:
            if not data.get("name_lock", False):
                self.name.unlock()
            else:
                self.name.lock()

        if data.get("localized_name") is not None:
            self.localized_name.set_value(data.get("localized_name"), force)

        if data.get("localized_name_lock") is not None:
            if not data.get("localized_name_lock", False):
                self.localized_name.unlock()
            else:
                self.localized_name.lock()
        
        if data.get("alt_names") is not None:
            self.add_alternative_names(data.get("alt_names", []))

        if data.get("alt_names_lock") is not None:
            if not data.get("alt_names_lock", False):
                self.alt_names.unlock()
            else:
                self.alt_names.lock()

        if data.get("description") is not None:
            self.description.set_value(data.get("description"), force)

        if data.get("description_lock") is not None:
            if not data.get("description_lock", False):
                self.description.unlock()
            else:
                self.description.lock()

        if data.get("genres") is not None:
            self.genres.set_value(data.get("genres"), force)

        if data.get("genres_lock") is not None:
            if not data.get("genres_lock", False):
                self.genres.unlock()
            else:
                self.genres.lock()

        if data.get("tags") is not None:
            self.tags.set_value(data.get("tags"), force)

        if data.get("tags_lock") is not None:
            if not data.get("tags_lock", False):
                self.tags.unlock()
            else:
                self.tags.lock()

        if data.get("complete") is not None:
            self.complete.set_value(data.get("complete"), force)

        if data.get("complete_lock") is not None:
            if not data.get("complete_lock", False):
                self.complete.unlock()
            else:
                self.complete.lock()

        self.arguments = {**self.arguments, **data}
        self.save()

    def to_representation(self):
        return {
            "name": {
                "type": "string",
                "label": pgettext("Name field name for Manga", "database.models.manga.name"),
                "value": self.name.value,
                "locked": self.name.locked
                },
            "complete": {
                "type": "bool",
                "label": pgettext("Name field complete for Manga", "database.models.manga.complete"),
                "value": self.complete.value,
                "locked": self.complete.locked
                },
            "localized_name": {
                "type": "string",
                "label": pgettext("Localized name field name for Manga", "database.models.manga.localized_name"),
                "value": self.localized_name.value,
                "locked": self.localized_name.locked
                },
            "description": {
                "type": "long_string",
                "label": pgettext("Description field name for Manga", "database.models.manga.description"),
                "value": self.description.value,
                "locked": self.description.locked
                },
            "genres": {
                "type": "list",
                "label": pgettext("Genres field name for Manga", "database.models.manga.genres"),
                "value": self.genres.value,
                "locked": self.genres.locked
                },
            "tags": {
                "type": "list",
                "label": pgettext("Tags field name for Manga", "database.models.manga.tags"),
                "value": self.tags.value,
                "locked": self.tags.locked
                },
        }

    def get_fields_values_for_xml(self) -> dict:
        return {
            "Series": self.name.value,
            "LocalizedSeries": self.localized_name.value,
            "Summary": self.description.value,
            "Genre": ", ".join(self.genres.value),
            "Tags": ", ".join(self.tags.value),
            "Web": self.url,
        }
    
    
    def json_serialized(self) -> dict:
        output = {}
        for field in self._meta.get_fields():
            if not hasattr(self, field.name):
                continue
            name = getattr(self, field.name)
            if hasattr(name, "value"):
                value = name.value
                if isinstance(value, datetime):
                    output[field.name] = value.strftime("%Y-%m-%dT%H:%M:%S%z")
                else:
                    output[field.name] = value
        output["id"] = self.id
        output["cover"] = self.cover
        return output

class MangaANLink(BaseModel):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, related_name="alternative_names")
    alternative_name = LockableCharField(verbose_name=pgettext("Alternative names field name for MangaANLink", "database.models.manga.alternative_name"))

    def __str__(self) -> str:
        return self.alternative_name.value
    
class Volume(BaseModel):
    name = LockableCharField(verbose_name=pgettext("Name field name for Volume", "database.models.volume.name"))
    description = LockableCharField(verbose_name=pgettext("Description field name for Volume", "database.models.volume.description"))
    number = LockableFloatField(verbose_name=pgettext("Number field name for Volume", "database.models.volume.number"))
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, related_name="volumes", verbose_name=pgettext("Mange FK field name for Volume", "processes.models.volume.manga"))
    arguments = models.JSONField(default=dict, verbose_name=pgettext("Arguments JSON field name for Volume", "processes.models.volume.arguments"), blank=True)

    @property
    def volume(self):
        if isinstance(self.number.value, float) and self.number.value.is_integer():
            return int(self.number.value)
        return self.number.value

    def __str__(self) -> str:
        if len(self.name.value) > 0:
            return self.name.value
        return f'{self.manga.__str__()} Vol.{self.volume}'
    
    def update_fields(self, data:dict, force:bool = False) -> None:
        if data.get("name") is not None:
            self.name.set_value(data.get("name"), force)

        if data.get("name_lock") is not None:
            if not data.get("name_lock", False):
                self.name.unlock()
            else:
                self.name.lock()

        if data.get("description") is not None:
            self.description.set_value(data.get("description"), force)

        if data.get("description_lock") is not None:
            if not data.get("description_lock", False):
                self.description.unlock()
            else:
                self.description.lock()

        if data.get("volume_number") is not None:
            self.number.set_value(data.get("volume_number"), force)

        if data.get("volume_number_lock") is not None:
            if not data.get("volume_number_lock", False):
                self.number.unlock()
            else:
                self.number.lock()

        self.arguments = {**self.arguments, **data}
        self.save()

    def to_representation(self):
        return {
            "name": {
                "type": "string",
                "label": pgettext("Name field name for Volume", "database.models.volume.name"),
                "value": self.name.value,
                "locked": self.name.locked
                },
            "description": {
                "type": "long_string",
                "label": pgettext("Description field name for Volume", "database.models.volume.description"),
                "value": self.description.value,
                "locked": self.description.locked
                },
            "volume_number": {
                "type": "float",
                "label": pgettext("Number field name for Volume", "database.models.volume.number"),
                "value": self.number.value,
                "locked": self.number.locked
                },
        }

    def get_fields_values_for_xml(self) -> dict:
        return {
            **self.manga.get_fields_values_for_xml(),
            **({"Summary": self.description.value} if len(self.description.value) > 0 else {}),
            "Volume": self.volume,
        }
    
    
    def json_serialized(self) -> dict:
        output = {}
        for field in self._meta.get_fields():
            if not hasattr(self, field.name):
                continue
            name = getattr(self, field.name)
            if hasattr(name, "value"):
                value = name.value
                if isinstance(value, datetime):
                    output[field.name] = value.strftime("%Y-%m-%dT%H:%M:%S%z")
                else:
                    output[field.name] = value
        output["manga_id"] = self.manga.id
        output["cover"] = self.manga.cover
        return output
    
class Chapter(BaseModel):
    name = LockableCharField(verbose_name=pgettext("Name field name for Chapter", "database.models.chapter.name"))
    description = LockableCharField(verbose_name=pgettext("Description field name for Chapter", "database.models.chapter.description"))
    localization = LockableCharField(verbose_name=pgettext("Localization field name for Chapter", "database.models.chapter.localization"))
    publisher = LockableListField(verbose_name=pgettext("Publisher field name for Chapter", "database.models.chapter.publisher"))
    imprint = LockableListField(verbose_name=pgettext("Imprint field name for Chapter", "database.models.chapter.imprint"))
    release_date = LockableDateTimeField(verbose_name=pgettext("Release date field name for Chapter", "database.models.chapter.release_date"))
    writer = LockableListField(verbose_name=pgettext("Writer field name for Chapter", "database.models.chapter.writer"))
    penciller = LockableListField(verbose_name=pgettext("Penciller field name for Chapter", "database.models.chapter.penciller"))
    inker = LockableListField(verbose_name=pgettext("Inker field name for Chapter", "database.models.chapter.inker"))
    colorist = LockableListField(verbose_name=pgettext("Colorist field name for Chapter", "database.models.chapter.colorist"))
    letterer = LockableListField(verbose_name=pgettext("Letterer field name for Chapter", "database.models.chapter.letterer"))
    cover_artist = LockableListField(verbose_name=pgettext("Cover artist field name for Chapter", "database.models.chapter.cover_artist"))
    editor = LockableListField(verbose_name=pgettext("Editor field name for Chapter", "database.models.chapter.editor"))
    translator = LockableListField(verbose_name=pgettext("Translator field name for Chapter", "database.models.chapter.translator"))
    page_count = LockableIntegerField(default=0, verbose_name=pgettext("Page count field name for Chapter", "database.models.chapter.page_count"))
    format = LockableEnumField(enum_class=Formats, default=Formats.NORMAL, verbose_name=pgettext("Format field name for Chapter", "database.models.chapter.format"))
    age_rating = LockableEnumField(enum_class=AgeRating, default=AgeRating.UNKNOWN, verbose_name=pgettext("Age rating field name for Chapter", "database.models.chapter.age_rating"))
    isbn = LockableCharField(verbose_name=pgettext("ISBN field name for Chapter", "database.models.chapter.isbn"))
    number = LockableFloatField(default=1.0, verbose_name=pgettext("Number field name for Chapter", "database.models.chapter.number"))
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE, related_name="chapters", verbose_name=pgettext("Volume FK field name for Chapter", "database.models.chapter.volume"))
    file = models.CharField(max_length=512, default=FILE_PATH_ROOT, verbose_name=pgettext("File field name for Chapter", "database.models.chapter.file_path"))
    url = models.URLField(verbose_name=pgettext("URL field name for Chapter", "database.models.chapter.url"), unique=True)
    source_url = models.URLField(verbose_name=pgettext("Source URL field name for Chapter", "database.models.chapter.source_url"))
    downloaded = models.BooleanField(default=False, verbose_name=pgettext("Downloaded field name for Chapter", "database.models.chapter.downloaded"))
    arguments = models.JSONField(default=dict, verbose_name=pgettext("Arguments JSON field name for Chapter", "processes.models.manga.arguments"), blank=True)

    @property
    def chapter(self):
        if isinstance(self.number.value, float) and self.number.value.is_integer():
            return int(self.number.value)
        return self.number.value

    def __str__(self) -> str:
        if len(self.name.value) > 0:
            return self.name.value
        return f'{self.volume.__str__()} Ch.{self.chapter}'
    
    def update_fields(self, data:dict, force:bool = False) -> None:
        if data.get("name") is not None:
            self.name.set_value(data.get("name"), force)

        if data.get("name_lock") is not None:
            if not data.get("name_lock", False):
                self.name.unlock()
            else:
                self.name.lock()


            
        if data.get("description") is not None:
            self.description.set_value(data.get("description"), force)

        if data.get("description_lock") is not None:
            if not data.get("description_lock", False):
                self.description.unlock()
            else:
                self.description.lock()


            
        if data.get("localization") is not None:
            self.localization.set_value(data.get("localization"), force)

        if data.get("localization_lock") is not None:
            if not data.get("localization_lock", False):
                self.localization.unlock()
            else:
                self.localization.lock()


            
        if data.get("publisher") is not None:
            self.publisher.set_value(data.get("publisher"), force)

        if data.get("publisher_lock") is not None:
            if not data.get("publisher_lock", False):
                self.publisher.unlock()
            else:
                self.publisher.lock()


            
        if data.get("imprint") is not None:
            self.imprint.set_value(data.get("imprint"), force)

        if data.get("imprint_lock") is not None:
            if not data.get("imprint_lock", False):
                self.imprint.unlock()
            else:
                self.imprint.lock()


            
        if data.get("release_date") is not None:
            self.release_date.set_value(data.get("release_date"), force)

        if data.get("release_date_lock") is not None:
            if not data.get("release_date_lock", False):
                self.release_date.unlock()
            else:
                self.release_date.lock()



            
        if data.get("writer") is not None:
            self.writer.set_value(data.get("writer"), force)

        if data.get("writer_lock") is not None:
            if not data.get("writer_lock", False):
                self.writer.unlock()
            else:
                self.writer.lock()


            

        if data.get("penciller") is not None:
            self.penciller.set_value(data.get("penciller"), force)

        if data.get("penciller_lock") is not None:
            if not data.get("penciller_lock", False):
                self.penciller.unlock()
            else:
                self.penciller.lock()



            
        if data.get("inker") is not None:
            self.inker.set_value(data.get("inker"), force)

        if data.get("inker_lock") is not None:
            if not data.get("inker_lock", False):
                self.inker.unlock()
            else:
                self.inker.lock()


            
            
        if data.get("colorist") is not None:
            self.colorist.set_value(data.get("colorist"), force)

        if data.get("colorist_lock") is not None:
            if not data.get("colorist_lock", False):
                self.colorist.unlock()
            else:
                self.colorist.lock()


            
            
        if data.get("letterer") is not None:
            self.letterer.set_value(data.get("letterer"), force)

        if data.get("letterer_lock") is not None:
            if not data.get("letterer_lock", False):
                self.letterer.unlock()
            else:
                self.letterer.lock()


            
            
        if data.get("cover_artist") is not None:
            self.cover_artist.set_value(data.get("cover_artist"), force)

        if data.get("cover_artist_lock") is not None:
            if not data.get("cover_artist_lock", False):
                self.cover_artist.unlock()
            else:
                self.cover_artist.lock()

            
            
            
        if data.get("editor") is not None:
            self.editor.set_value(data.get("editor"), force)

        if data.get("editor_lock") is not None:
            if not data.get("editor_lock", False):
                self.editor.unlock()
            else:
                self.editor.lock()

            
            
            
        if data.get("translator") is not None:
            self.translator.set_value(data.get("translator"), force)

        if data.get("translator_lock") is not None:
            if not data.get("translator_lock", False):
                self.translator.unlock()
            else:
                self.translator.lock()

            
        
            
        if data.get("page_count") is not None:
            self.page_count.set_value(data.get("page_count"), force)

        if data.get("page_count_lock") is not None:
            if not data.get("page_count_lock", False):
                self.page_count.unlock()
            else:
                self.page_count.lock()



            
        if data.get("format") is not None:
            self.format.set_value(Formats(int(data.get("format"))), force)

        if data.get("format_lock") is not None:
            if not data.get("format_lock", False):
                self.format.unlock()
            else:
                self.format.lock()



            
        if data.get("age_rating") is not None:
            self.age_rating.set_value(AgeRating(int(data.get("age_rating"))), force)

        if data.get("age_rating_lock") is not None:
            if not data.get("age_rating_lock", False):
                self.age_rating.unlock()
            else:
                self.age_rating.lock()



            
        if data.get("isbn") is not None:
            self.isbn.set_value(data.get("isbn"), force)

        if data.get("isbn_lock") is not None:
            if not data.get("isbn_lock", False):
                self.isbn.unlock()
            else:
                self.isbn.lock()



            
        if data.get("chapter_number") is not None:
            self.number.set_value(data.get("chapter_number"), force)

        if data.get("chapter_number_lock") is not None:
            if not data.get("chapter_number_lock", False):
                self.number.unlock()
            else:
                self.number.lock()


            
        if data.get("source_url") is not None:
            self.source_url = data.get("source_url")
            
        self.arguments = {**self.arguments, **data}
        self.save()
        
    def to_representation(self):
        return {
            "name": {
                "type": "string",
                "label": pgettext("Name field name for Chapter", "database.models.chapter.name"),
                "value": self.name.value,
                "locked": self.name.locked
                },
            "description": {
                "type": "long_string",
                "label": pgettext("Description field name for Chapter", "database.models.chapter.description"),
                "value": self.description.value,
                "locked": self.description.locked
                },
            "publisher": {
                "type": "list",
                "label": pgettext("Publisher field name for Chapter", "database.models.chapter.publisher"),
                "value": self.publisher.value,
                "locked": self.publisher.locked
                },
            "imprint": {
                "type": "list",
                "label": pgettext("Imprint field name for Chapter", "database.models.chapter.imprint"),
                "value": self.imprint.value,
                "locked": self.imprint.locked
                },
            "release_date": {
                "type": "date",
                "label": pgettext("Release date field name for Chapter","database.models.chapter.release_date"),
                "value": self.release_date.value,
                "locked": self.release_date.locked
                },
            "writer": {
                "type": "list",
                "label": pgettext("Writer field name for Chapter", "database.models.chapter.writer"),
                "value": self.writer.value,
                "locked": self.writer.locked
                },
            "penciller": {
                "type": "list",
                "label": pgettext("Penciller field name for Chapter", "database.models.chapter.penciller"),
                "value": self.penciller.value,
                "locked": self.penciller.locked
                },
            "inker": {
                "type": "list",
                "label": pgettext("Inker field name for Chapter", "database.models.chapter.inker"),
                "value": self.inker.value,
                "locked": self.inker.locked
                },
            "colorist": {
                "type": "list",
                "label": pgettext("Colorist field name for Chapter", "database.models.chapter.colorist"),
                "value": self.colorist.value,
                "locked": self.colorist.locked
                },
            "letterer": {
                "type": "list",
                "label": pgettext("Letterer field name for Chapter", "database.models.chapter.letterer"),
                "value": self.letterer.value,
                "locked": self.letterer.locked
                },
            "cover_artist": {
                "type": "list",
                "label": pgettext("Cover artist field name for Chapter", "database.models.chapter.cover_artist"),
                "value": self.cover_artist.value,
                "locked": self.cover_artist.locked
                },
            "editor": {
                "type": "list",
                "label": pgettext("Editor field name for Chapter", "database.models.chapter.editor"),
                "value": self.editor.value,
                "locked": self.editor.locked
                },
            "translator": {
                "type": "list",
                "label": pgettext("Translator field name for Chapter", "database.models.chapter.translator"),
                "value": self.translator.value,
                "locked": self.translator.locked
                },
            "page_count": {
                "type": "int",
                "label": pgettext("Page count field name for Chapter", "database.models.chapter.page_count"),
                "value": self.page_count.value,
                "locked": self.page_count.locked
                },
            "format": {
                "type": "choice",
                "label": pgettext("Format field name for Chapter", "database.models.chapter.format"),
                "value": self.format.value,
                "locked": self.format.locked,
                "choices": [{"value": v, "text": l or n.title() }for v, n, l in Formats.get_members(Formats)]
                },
            "age_rating": {
                "type": "choice",
                "label": pgettext("Age rating field name for Chapter", "database.models.chapter.age_rating"),
                "value": self.age_rating.value,
                "locked": self.age_rating.locked,
                "choices": [{"value": v, "text": l or n.title() }for v, n, l in AgeRating.get_members(AgeRating)]
                },
            "isbn": {
                "type": "string",
                "label": pgettext("ISBN field name for Chapter", "database.models.chapter.isbn"),
                "value": self.isbn.value,
                "locked": self.isbn.locked
                },
            "chapter_number": {
                "type": "float",
                "label": pgettext("Number field name for Chapter", "database.models.chapter.number"),
                "value": self.number.value,
                "locked": self.number.locked
                },
        }

    def get_file_name(self) -> str:
        return make_valid_filename(f"{self.volume.manga.name.value} - Vol. {self.volume.volume} Ch. {self.chapter}.cbz")

    def get_fields_values_for_xml(self) -> dict:
        date = self.release_date.value
        return {
            **self.volume.get_fields_values_for_xml(),
            "Title": self.name.value,
            "Number": self.chapter,
            **({"Summary": self.description.value} if len(self.description.value) > 0 else {}),
            "Publisher": ", ".join(self.publisher.value),
            "Imprint": ", ".join(self.imprint.value),
            "Year": date.year,
            "Month": date.month,
            "Day": date.day,
            "Writer": ", ".join(self.writer.value),
            "Penciller": ", ".join(self.penciller.value),
            "Inker": ", ".join(self.inker.value),
            "Colorist": ", ".join(self.colorist.value),
            "Letterer": ", ".join(self.letterer.value),
            "CoverArtist": ", ".join(self.cover_artist.value),
            "Editor": ", ".join(self.editor.value),
            "Translator": ", ".join(self.translator.value),
            "PageCount": self.page_count.value,
            "LanguageISO": self.localization.value,
            "Format": self.format.value.label,
            "AgeRating": self.age_rating.value.label,
            "GTIN": self.isbn.value,
        }

    def create_xml(self) -> str:
        root = ET.Element("ComicInfo")

        for tag, text in self.get_fields_values_for_xml().items():
            if text is None:
                continue
            ET.SubElement(root, tag).text = unescape(str(text))

        xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        reparsed = minidom.parseString(xml_bytes)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    
    
    def json_serialized(self) -> dict:
        output = {}
        for field in self._meta.get_fields():
            if not hasattr(self, field.name):
                continue
            name = getattr(self, field.name)
            if hasattr(name, "value"):
                value = name.value
                if isinstance(value, datetime):
                    output[field.name] = value.strftime("%Y-%m-%dT%H:%M:%S%z")
                else:
                    output[field.name] = value
        output["manga_id"] = self.volume.manga.id
        output["cover"] = self.volume.manga.cover
        return output