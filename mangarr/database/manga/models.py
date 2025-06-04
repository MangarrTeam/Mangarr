from django.db import models
from django.utils.translation import pgettext
from database.data_types.models import StringType, BoolType, IntType, FloatType, DateType, FormatsEnumType, AgeRatingEnumType, StatusEnumType
from datetime import datetime
from django.utils import timezone
from plugins.base import Formats, AgeRating
from plugins.utils import get_downloaded_metadata
from django.contrib.auth.models import User
from plugins.base import MangaPluginBase, NO_THUMBNAIL_URL
from plugins.functions import get_plugin_by_key
from django.db.models.signals import post_delete
from django.dispatch import receiver
from server.settings import FILE_PATH_ROOT
import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.sax.saxutils import unescape
import hashlib
from .functions import make_valid_filename


# Create your models here.
def get_choices() -> list[tuple]:
    return [
        (f'{pm["category"]}_{pm["domain"]}', f'{pm["name"]} ({pm["category"]})')
        for pm in get_downloaded_metadata()
        if pm.get("category") and pm.get("domain") and pm.get("name")
    ]

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

class MangaRequest(models.Model):
    plugin = models.CharField(max_length=64, choices=get_choices(), verbose_name=pgettext("Plugin field name for MangaRequest", "database.models.manga_request.plugin"))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=pgettext("User FK field name for MangaRequest", "database.models.manga_request.requested_by"))
    variables = models.JSONField(default=dict, blank=True, verbose_name=pgettext("Variables JSON field name for MangaRequest", "database.models.manga_request.variables"))


    @staticmethod
    def has_plugin(category:str, domain:str) -> bool:
        return any([ch[0] == f'{category}_{domain}' for ch in get_choices()])
    
    def get_plugin(self) -> MangaPluginBase:
        return get_plugin_by_key(self.plugin)    

    def choose_plugin(self, category:str, domain:str) -> None:
        choices = get_choices()
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
    
from django.db.models.fields.related import OneToOneField, ManyToManyField, ManyToOneRel, ForeignKey
from django.db.models.fields import DateTimeField, CharField

class Manga(models.Model):
    plugin = models.CharField(max_length=64, choices=get_choices(), verbose_name=pgettext("Plugin field name for Manga", "database.models.manga_request.plugin"))
    name = models.OneToOneField(StringType, on_delete=models.PROTECT, null=True, verbose_name=pgettext("Name field name for Manga", "database.models.manga.name"), related_name="manga_name")
    localized_name = models.OneToOneField(StringType, on_delete=models.PROTECT, null=True, verbose_name=pgettext("Localized name field name for Manga", "database.models.manga.localized_name"), related_name="manga_localized_name")
    description = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Description field name for Manga", "database.models.manga.description"), related_name="manga_description")
    genres = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Genres field name for Manga", "database.models.manga.genres"), related_name="manga_genres")
    tags = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Tags field name for Manga", "database.models.manga.tags"), related_name="manga_tags")
    date_added = models.DateTimeField(auto_now_add=True, verbose_name=pgettext("Date added field name for Manga", "database.models.manga.date_added"))
    last_update = models.DateTimeField(auto_now_add=True, verbose_name=pgettext("Last update field name for Manga", "database.models.manga.last_update"))
    complete = models.BooleanField(default=False, verbose_name=pgettext("Complete field name for Manga", "database.models.manga.complete"))
    url = models.URLField(verbose_name=pgettext("URL field name for Manga", "database.models.manga.url"), unique=True)
    folder = models.CharField(max_length=512, default=FILE_PATH_ROOT, verbose_name=pgettext("Folder field name for Manga", "database.models.manga.folder_path"))
    arguments = models.JSONField(default=dict, verbose_name=pgettext("Arguments JSON field name for Manga", "processes.models.manga.arguments"), blank=True)

    def __str__(self) -> str:
        return self.name.value
    
    @property
    def cover(self) -> str:
        return self.arguments.get("cover", NO_THUMBNAIL_URL)

    @staticmethod
    def monitor_exist(url:str) -> bool:
        return Manga.objects.filter(url=url).exists()
    
    def set_folder_path(self, name:str="") -> None:
        if len(name) == 0:
            name = get_hash(self.url)

        self.folder = FILE_PATH_ROOT / f"{make_valid_filename(name)}"

    def choose_plugin(self, key:str) -> None:
        if self.plugin is not None and len(self.plugin) > 0:
            return
        choices = get_choices()
        if not any([ch[0] == key for ch in choices]):
            return
        
        for choice in choices:
            if choice[0] == key:
                self.plugin = choice[0]
    
    def add_alternative_names(self, alternative_names:list):
        for alternative_name in alternative_names:
            alt_name = StringType()
            alt_name.value = alternative_name
            alt_name.save()
            self.alternative_names.create(manga=self, alternative_names=alt_name)

    def update_last_update(self) -> None:
        self.last_update = timezone.now()
        self.save()

    def update_fields(self, data:dict, force:bool = False) -> None:
        if data.get("name") is not None:
            if force:
                self.name.value_force(data.get("name"))
            else:
                self.name.value = data.get("name")

        if data.get("name_lock") is not None:
            if not data.get("name_lock", False):
                self.name.unlock()
            else:
                self.name.lock()

        if data.get("localized_name") is not None:
            if force:
                self.localized_name.value_force(data.get("localized_name"))
            else:
                self.localized_name.value = data.get("localized_name")

        if data.get("localized_name_lock") is not None:
            if not data.get("localized_name_lock", False):
                self.localized_name.unlock()
            else:
                self.localized_name.lock()
        
        if data.get("alt_names") is not None:
            self.add_alternative_names(data.get("alt_names"))

        if data.get("alt_names_lock") is not None:
            if not data.get("alt_names_lock", False):
                self.alt_names.unlock()
            else:
                self.alt_names.lock()

        if data.get("description") is not None:
            if force:
                self.description.value_force(data.get("description"))
            else:
                self.description.value = data.get("description")

        if data.get("description_lock") is not None:
            if not data.get("description_lock", False):
                self.description.unlock()
            else:
                self.description.lock()

        if data.get("genres") is not None:
            if force:
                self.genres.value_force(", ".join(data.get("genres")))
            else:
                self.genres.value = ", ".join(data.get("genres"))

        if data.get("genres_lock") is not None:
            if not data.get("genres_lock", False):
                self.genres.unlock()
            else:
                self.genres.lock()

        if data.get("tags") is not None:
            if force:
                self.tags.value_force(", ".join(data.get("tags")))
            else:
                self.tags.value = ", ".join(data.get("tags"))

        if data.get("tags_lock") is not None:
            if not data.get("tags_lock", False):
                self.tags.unlock()
            else:
                self.tags.lock()

        if data.get("complete") is not None:
            self.complete = data.get("complete")

        self.arguments = {**self.arguments, **data}
        self.save()

    def to_representation(self):
        return {
            "name": {"type": "string", "label": pgettext("Name field name for Manga", "database.models.manga.name"),"value": self.name.value, "locked": self.name.locked},
            "localized_name": {"type": "string", "label": pgettext("Localized name field name for Manga", "database.models.manga.localized_name"),"value": self.localized_name.value, "locked": self.localized_name.locked},
            "description": {"type": "long_string", "label": pgettext("Description field name for Manga", "database.models.manga.description"),"value": self.description.value, "locked": self.description.locked},
            "genres": {"type": "list", "label": pgettext("Genres field name for Manga", "database.models.manga.genres"),"value": self.genres.value.split(", "), "locked": self.genres.locked},
            "tags": {"type": "list", "label": pgettext("Tags field name for Manga", "database.models.manga.tags"),"value": self.tags.value.split(", "), "locked": self.tags.locked},
        }
    
    def save(self, *args, **kwargs):
        for field in self._meta.get_fields():
            if isinstance(field, OneToOneField):
                current_value = getattr(self, field.name)
                if current_value is None:
                    new_item = field.related_model.objects.create()
                    setattr(self, field.name, new_item)
        super().save(*args, **kwargs)

    def json_serialized(self) -> dict:
        output = {}
        for field in self._meta.get_fields():
            if not hasattr(self, field.name):
                continue
            if isinstance(field, OneToOneField):
                output[field.name] = getattr(self, field.name).value_str
            elif isinstance(field, ManyToOneRel):
                output[field.name] = [str(item) for item in getattr(self, field.name).all()]
            elif isinstance(field, ForeignKey):
                output[field.name] = str(getattr(self, field.name))
            elif isinstance(field, DateTimeField):
                output[field.name] = getattr(self, field.name).strftime("%Y-%m-%dT%H:%M:%S%z")
            else:
                output[field.name] = getattr(self, field.name)
        output["cover"] = self.cover
        return output

    def get_fields_values_for_xml(self) -> dict:
        return {
            "Series": self.name.value,
            "LocalizedSeries": self.localized_name.value,
            "Summary": self.description.value,
            "Genre": self.genres.value,
            "Tags": self.tags.value,
            "Web": self.url,
        }

class MangaANLink(models.Model):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, related_name="alternative_names")
    alternative_names = models.OneToOneField(StringType, on_delete=models.PROTECT, verbose_name=pgettext("Alternative names field name for MangaANLink", "database.models.manga.alternative_names"), related_name="manga_alternative_names")

    def __str__(self) -> str:
        return self.alternative_names.value_str

class Volume(models.Model):
    name = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Name field name for Volume", "database.models.volume.name"), related_name="volume_name")
    description = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Description field name for Volume", "database.models.volume.description"), related_name="volume_description")
    number = models.OneToOneField(FloatType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Number field name for Volume", "database.models.volume.number"), related_name="volume_number")
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
    
    def save(self, *args, **kwargs):
        for field in self._meta.get_fields():
            if isinstance(field, OneToOneField):
                current_value = getattr(self, field.name)
                if current_value is None:
                    new_item = field.related_model.objects.create()
                    setattr(self, field.name, new_item)
        super().save(*args, **kwargs)

    def json_serialized(self) -> dict:
        output = {}
        for field in self._meta.get_fields():
            if not hasattr(self, field.name):
                continue
            if isinstance(field, OneToOneField):
                output[field.name] = getattr(self, field.name).value
            elif isinstance(field, ForeignKey):
                output[field.name] = str(getattr(self, field.name))
            else:
                output[field.name] = getattr(self, field.name)
        output["manga_id"] = self.manga.id
        output["cover"] = self.manga.cover
        return {}
    
    def update_fields(self, data:dict, force:bool = False) -> None:
        if data.get("name") is not None:
            if force:
                self.name.value_force(data.get("name"))
            else:
                self.name.value = data.get("name")

        if data.get("name_lock") is not None:
            if not data.get("name_lock", False):
                self.name.unlock()
            else:
                self.name.lock()

        if data.get("description") is not None:
            if force:
                self.description.value_force(data.get("description"))
            else:
                self.description.value = data.get("description")

        if data.get("description_lock") is not None:
            if not data.get("description_lock", False):
                self.description.unlock()
            else:
                self.description.lock()

        if data.get("volume_number") is not None:
            if force:
                self.number.value_force(data.get("volume_number"))
            else:
                self.number = data.get("volume_number")

        if data.get("volume_number_lock") is not None:
            if not data.get("volume_number_lock", False):
                self.number.unlock()
            else:
                self.number.lock()

        self.arguments = {**self.arguments, **data}
        self.save()

    def to_representation(self):
        return {
            "name": {"type": "string", "label": pgettext("Name field name for Volume", "database.models.volume.name"),"value": self.name.value, "locked": self.name.locked},
            "description": {"type": "long_string", "label": pgettext("Description field name for Volume", "database.models.volume.description"),"value": self.description.value, "locked": self.description.locked},
            "volume_number": {"type": "float", "label": pgettext("Number field name for Volume", "database.models.volume.number"),"value": self.number.value, "locked": self.number.locked},
        }

    def get_fields_values_for_xml(self) -> dict:
        return {
            **self.manga.get_fields_values_for_xml(),
            **({"Summary": self.description.value} if len(self.description.value) > 0 else {}),
            "Volume": self.volume,
        }

class Chapter(models.Model):
    name = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Name field name for Chapter", "database.models.chapter.name"), related_name="chapter_name")
    description = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Description field name for Chapter", "database.models.chapter.description"), related_name="chapter_description")
    localization = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Localization field name for Chapter", "database.models.chapter.localization"), related_name="chapter_localization")
    publisher = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Publisher field name for Chapter", "database.models.chapter.publisher"), related_name="chapter_publisher")
    imprint = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Imprint field name for Chapter", "database.models.chapter.imprint"), related_name="chapter_imprint")
    release_date = models.OneToOneField(DateType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Release date field name for Chapter", "database.models.chapter.release_date"), related_name="chapter_release_date")
    writer = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Writer field name for Chapter", "database.models.chapter.writer"), related_name="chapter_writer")
    penciller = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Penciller field name for Chapter", "database.models.chapter.penciller"), related_name="chapter_penciller")
    inker = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Inker field name for Chapter", "database.models.chapter.inker"), related_name="chapter_inker")
    colorist = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Colorist field name for Chapter", "database.models.chapter.colorist"), related_name="chapter_colorist")
    letterer = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Letterer field name for Chapter", "database.models.chapter.letterer"), related_name="chapter_letterer")
    cover_artist = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Cover artist field name for Chapter", "database.models.chapter.cover_artist"), related_name="chapter_cover_artist")
    editor = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Editor field name for Chapter", "database.models.chapter.editor"), related_name="chapter_editor")
    translator = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Translator field name for Chapter", "database.models.chapter.translator"), related_name="chapter_translator")
    page_count = models.OneToOneField(IntType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Page count field name for Chapter", "database.models.chapter.page_count"), related_name="chapter_page_count")
    format = models.OneToOneField(FormatsEnumType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Format field name for Chapter", "database.models.chapter.format"), related_name="chapter_format")
    age_rating = models.OneToOneField(AgeRatingEnumType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Age rating field name for Chapter", "database.models.chapter.age_rating"), related_name="chapter_age_rating")
    isbn = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("ISBN field name for Chapter", "database.models.chapter.isbn"), related_name="chapter_isbn")
    number = models.OneToOneField(FloatType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=pgettext("Number field name for Chapter", "database.models.chapter.number"), related_name="chapter_number")
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
    
    def save(self, *args, **kwargs):
        for field in self._meta.get_fields():
            if isinstance(field, OneToOneField):
                current_value = getattr(self, field.name)
                if current_value is None:
                    related_model = field.related_model

                    default_value = None
                    if hasattr(field, 'default') and field.default is not models.NOT_PROVIDED:
                        default_value = field.default


                    new_instance = related_model.objects.create()

                    # Try setting a `.value` attribute if available
                    if default_value is not None and hasattr(new_instance, 'value'):
                        new_instance.value = default_value
                        new_instance.save()

                    setattr(self, field.name, new_instance)
        super().save(*args, **kwargs)

    def json_serialized(self) -> dict:
        output = {}
        for field in self._meta.get_fields():
            if not hasattr(self, field.name):
                continue
            if field.name == "file":
                continue
            if isinstance(field, OneToOneField):
                output[field.name] = getattr(self, field.name).value
            elif isinstance(field, ForeignKey):
                output[field.name] = str(getattr(self, field.name))
            else:
                output[field.name] = getattr(self, field.name)
        output["manga_id"] = self.volume.manga.id
        output["cover"] = self.volume.manga.cover
        return output
    
    def update_fields(self, data:dict, force:bool = False) -> None:
        if data.get("name") is not None:
            if force:
                self.name.value_force(data.get("name"))
            else:
                self.name.value = data.get("name")

        if data.get("name_lock") is not None:
            if not data.get("name_lock", False):
                self.name.unlock()
            else:
                self.name.lock()


            
        if data.get("description") is not None:
            if force:
                self.description.value_force(data.get("description"))
            else:
                self.description.value = data.get("description")

        if data.get("description_lock") is not None:
            if not data.get("description_lock", False):
                self.description.unlock()
            else:
                self.description.lock()


            
        if data.get("localization") is not None:
            if force:
                self.localization.value_force(data.get("localization"))
            else:
                self.localization.value = data.get("localization")

        if data.get("localization_lock") is not None:
            if not data.get("localization_lock", False):
                self.localization.unlock()
            else:
                self.localization.lock()


            
        if data.get("publisher") is not None:
            if force:
                self.publisher.value_force(", ".join(data.get("publisher")))
            else:
                self.publisher.value = ", ".join(data.get("publisher"))

        if data.get("publisher_lock") is not None:
            if not data.get("publisher_lock", False):
                self.publisher.unlock()
            else:
                self.publisher.lock()


            
        if data.get("imprint") is not None:
            if force:
                self.imprint.value_force(", ".join(data.get("imprint")))
            else:
                self.imprint.value = ", ".join(data.get("imprint"))

        if data.get("imprint_lock") is not None:
            if not data.get("imprint_lock", False):
                self.imprint.unlock()
            else:
                self.imprint.lock()


            
        if data.get("release_date") is not None:
            if force:
                self.release_date.value_force(data.get("release_date"))
            else:
                self.release_date.value = data.get("release_date")

        if data.get("release_date_lock") is not None:
            if not data.get("release_date_lock", False):
                self.release_date.unlock()
            else:
                self.release_date.lock()



            
        if data.get("writer") is not None:
            if force:
                self.writer.value_force(", ".join(data.get("writer")))
            else:
                self.writer.value = ", ".join(data.get("writer"))

        if data.get("writer_lock") is not None:
            if not data.get("writer_lock", False):
                self.writer.unlock()
            else:
                self.writer.lock()


            

        if data.get("penciller") is not None:
            if force:
                self.penciller.value_force(", ".join(data.get("penciller")))
            else:
                self.penciller.value = ", ".join(data.get("penciller"))

        if data.get("penciller_lock") is not None:
            if not data.get("penciller_lock", False):
                self.penciller.unlock()
            else:
                self.penciller.lock()



            
        if data.get("inker") is not None:
            if force:
                self.inker.value_force(", ".join(data.get("inker")))
            else:
                self.inker.value = ", ".join(data.get("inker"))

        if data.get("inker_lock") is not None:
            if not data.get("inker_lock", False):
                self.inker.unlock()
            else:
                self.inker.lock()


            
            
        if data.get("colorist") is not None:
            if force:
                self.colorist.value_force(", ".join(data.get("colorist")))
            else:
                self.colorist.value = ", ".join(data.get("colorist"))

        if data.get("colorist_lock") is not None:
            if not data.get("colorist_lock", False):
                self.colorist.unlock()
            else:
                self.colorist.lock()


            
            
        if data.get("letterer") is not None:
            if force:
                self.letterer.value_force(", ".join(data.get("letterer")))
            else:
                self.letterer.value = ", ".join(data.get("letterer"))

        if data.get("letterer_lock") is not None:
            if not data.get("letterer_lock", False):
                self.letterer.unlock()
            else:
                self.letterer.lock()


            
            
        if data.get("cover_artist") is not None:
            if force:
                self.cover_artist.value_force(", ".join(data.get("cover_artist")))
            else:
                self.cover_artist.value = ", ".join(data.get("cover_artist"))

        if data.get("cover_artist_lock") is not None:
            if not data.get("cover_artist_lock", False):
                self.cover_artist.unlock()
            else:
                self.cover_artist.lock()

            
            
            
        if data.get("editor") is not None:
            if force:
                self.editor.value_force(", ".join(data.get("editor")))
            else:
                self.editor.value = ", ".join(data.get("editor"))

        if data.get("editor_lock") is not None:
            if not data.get("editor_lock", False):
                self.editor.unlock()
            else:
                self.editor.lock()

            
            
            
        if data.get("translator") is not None:
            if force:
                self.translator.value_force(", ".join(data.get("translator")))
            else:
                self.translator.value = ", ".join(data.get("translator"))

        if data.get("translator_lock") is not None:
            if not data.get("translator_lock", False):
                self.translator.unlock()
            else:
                self.translator.lock()

            
        
            
        if data.get("page_count") is not None:
            if force:
                self.page_count.value_force(data.get("page_count"))
            else:
                self.page_count.value = data.get("page_count")

        if data.get("page_count_lock") is not None:
            if not data.get("page_count_lock", False):
                self.page_count.unlock()
            else:
                self.page_count.lock()



            
        if data.get("format") is not None:
            if force:
                self.format.value_force(Formats(int(data.get("format"))))
            else:
                self.format.value = Formats(int(data.get("format")))

        if data.get("format_lock") is not None:
            if not data.get("format_lock", False):
                self.format.unlock()
            else:
                self.format.lock()



            
        if data.get("age_rating") is not None:
            if force:
                self.age_rating.value_force(AgeRating(int(data.get("age_rating"))))
            else:
                self.age_rating.value = AgeRating(int(data.get("age_rating")))

        if data.get("age_rating_lock") is not None:
            if not data.get("age_rating_lock", False):
                self.age_rating.unlock()
            else:
                self.age_rating.lock()



            
        if data.get("isbn") is not None:
            if force:
                self.isbn.value_force(data.get("isbn"))
            else:
                self.isbn.value = data.get("isbn")

        if data.get("isbn_lock") is not None:
            if not data.get("isbn_lock", False):
                self.isbn.unlock()
            else:
                self.isbn.lock()



            
        if data.get("chapter_number") is not None:
            if force:
                self.number.value_force(data.get("chapter_number"))
            else:
                self.number.value = data.get("chapter_number")

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
            "name": {"type": "string", "label": pgettext("Name field name for Chapter", "database.models.chapter.name"),"value": self.name.value, "locked": self.name.locked},
            "description": {"type": "long_string", "label": pgettext("Description field name for Chapter", "database.models.chapter.description"),"value": self.description.value, "locked": self.description.locked},
            "publisher": {"type": "list", "label": pgettext("Publisher field name for Chapter", "database.models.chapter.publisher"),"value": self.publisher.value.split(", "), "locked": self.publisher.locked},
            "imprint": {"type": "list", "label": pgettext("Imprint field name for Chapter", "database.models.chapter.imprint"),"value": self.imprint.value.split(", "), "locked": self.imprint.locked},
            "release_date": {"type": "date", "label": pgettext("Release date field name for Chapter", "database.models.chapter.release_date"),"value": self.release_date.value, "locked": self.release_date.locked},
            "writer": {"type": "list", "label": pgettext("Writer field name for Chapter", "database.models.chapter.writer"),"value": self.writer.value.split(", "), "locked": self.writer.locked},
            "penciller": {"type": "list", "label": pgettext("Penciller field name for Chapter", "database.models.chapter.penciller"),"value": self.penciller.value.split(", "), "locked": self.penciller.locked},
            "inker": {"type": "list", "label": pgettext("Inker field name for Chapter", "database.models.chapter.inker"),"value": self.inker.value.split(", "), "locked": self.inker.locked},
            "colorist": {"type": "list", "label": pgettext("Colorist field name for Chapter", "database.models.chapter.colorist"),"value": self.colorist.value.split(", "), "locked": self.colorist.locked},
            "letterer": {"type": "list", "label": pgettext("Letterer field name for Chapter", "database.models.chapter.letterer"),"value": self.letterer.value.split(", "), "locked": self.letterer.locked},
            "cover_artist": {"type": "list", "label": pgettext("Cover artist field name for Chapter", "database.models.chapter.cover_artist"),"value": self.cover_artist.value.split(", "), "locked": self.cover_artist.locked},
            "editor": {"type": "list", "label": pgettext("Editor field name for Chapter", "database.models.chapter.editor"),"value": self.editor.value.split(", "), "locked": self.editor.locked},
            "translator": {"type": "list", "label": pgettext("Translator field name for Chapter", "database.models.chapter.translator"),"value": self.translator.value.split(", "), "locked": self.translator.locked},
            "page_count": {"type": "int", "label": pgettext("Page count field name for Chapter", "database.models.chapter.page_count"),"value": self.page_count.value, "locked": self.page_count.locked},
            "format": {"type": "choice", "label": pgettext("Format field name for Chapter", "database.models.chapter.format"),"value": self.format.value, "locked": self.format.locked, "choices": [{"value": v, "text": l or n.title() }for v, n, l in Formats.get_members(Formats)]},
            "age_rating": {"type": "choice", "label": pgettext("Age rating field name for Chapter", "database.models.chapter.age_rating"),"value": self.age_rating.value, "locked": self.age_rating.locked, "choices": [{"value": v, "text": l or n.title() }for v, n, l in AgeRating.get_members(AgeRating)]},
            "isbn": {"type": "string", "label": pgettext("ISBN field name for Chapter", "database.models.chapter.isbn"),"value": self.isbn.value.split(", "), "locked": self.isbn.locked},
            "chapter_number": {"type": "float", "label": pgettext("Number field name for Chapter", "database.models.chapter.number"),"value": self.number.value, "locked": self.number.locked},
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
            "Publisher": self.publisher.value,
            "Imprint": self.imprint.value,
            "Year": date.year,
            "Month": date.month,
            "Day": date.day,
            "Writer": self.writer.value,
            "Penciller": self.penciller.value,
            "Inker": self.inker.value,
            "Colorist": self.colorist.value,
            "Letterer": self.letterer.value,
            "CoverArtist": self.cover_artist.value,
            "Editor": self.editor.value,
            "Translator": self.translator.value,
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


def delete_related_objects(instance):
    for field in instance._meta.get_fields():
        if field.auto_created and not field.concrete:
            continue

        if isinstance(field, (OneToOneField, ForeignKey)):
            try:
                related_obj = getattr(instance, field.name)
            except Exception:
                continue

            if related_obj:
                related_obj.delete()
        elif isinstance(field, ManyToManyField):
            try:
                related_manager = getattr(instance, field.name)
                for obj in related_manager.all():
                    obj.delete()
            except Exception:
                continue

@receiver(post_delete, sender=Manga)
@receiver(post_delete, sender=Volume)
@receiver(post_delete, sender=Chapter)
@receiver(post_delete, sender=MangaANLink)
def delete_types(sender, instance, **kwargs):
    try:
        delete_related_objects(instance)
    finally:
        pass