from django.db import models
from django.utils.translation import gettext_lazy as _
from database.data_types.models import StringType, BoolType, IntType, FloatType, DateType, FormatsEnumType, AgeRatingEnumType, StatusEnumType
from plugins.base import Formats, AgeRating
from plugins.utils import get_downloaded_metadata
from django.contrib.auth.models import User
from plugins.base import MangaPluginBase
from plugins.functions import get_plugin_by_key
from django.db.models.signals import post_delete 
from django.dispatch import receiver
from server.settings import FILE_PATH_ROOT
import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.sax.saxutils import escape
from .functions import make_valid_filename


# Create your models here.
def get_choices() -> list[tuple]:
    return [
        (f'{pm["category"]}_{pm["domain"]}', f'{pm["name"]} ({pm["category"]})')
        for pm in get_downloaded_metadata()
        if pm.get("category") and pm.get("domain") and pm.get("name")
    ]

class MangaRequest(models.Model):
    plugin = models.CharField(max_length=64, choices=get_choices(), verbose_name=_("database.models.manga_request.plugin"))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("database.models.manga_request.requested_by"))
    variables = models.JSONField(default=dict, blank=True, verbose_name=_("database.models.manga_request.variables"))


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
    
    def save(self):
        if self.variables.get("url") is None:
            raise Exception("The variables need at least 'url'")

        super().save()

    def __str__(self):
        return f'{self.variables["name"] if self.variables.get("name") else self.get("url")} ({self.get_plugin_display()})'
    
from django.db.models.fields.related import OneToOneField, ManyToManyField, ForeignKey

class Manga(models.Model):
    plugin = models.CharField(max_length=64, choices=get_choices(), verbose_name=_("database.models.manga_request.plugin"))
    name = models.OneToOneField(StringType, on_delete=models.PROTECT, null=True, verbose_name=_("database.models.manga.name"), related_name="manga_name")
    localized_name = models.OneToOneField(StringType, on_delete=models.PROTECT, null=True, verbose_name=_("database.models.manga.localized_name"), related_name="manga_localized_name")
    description = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.manga.description"), related_name="manga_description")
    genres = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.manga.genres"), related_name="manga_genres")
    tags = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.manga.tags"), related_name="manga_tags")
    date_added = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    url = models.URLField(verbose_name=_("database.models.manga.url"), unique=True)
    arguments = models.JSONField(default=dict, verbose_name=_("processes.models.manga.arguments"), blank=True)

    def __str__(self) -> str:
        return self.name.value

    @staticmethod
    def monitor_exist(url:str) -> bool:
        return Manga.objects.filter(url=url).exists()

    def choose_plugin(self, key:str) -> None:
        if self.plugin is not None:
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

    def update_fields(self, data:dict) -> None:
        self.choose_plugin(self.plugin)
            
        if data.get("name"):
            self.name.value = data.get("name")
        
        if data.get("alt_names"):
            self.add_alternative_names(data.get("alt_names"))

        if data.get("description"):
            self.description.value = data.get("description")

        if data.get("genres"):
            self.genres.value = ", ".join(data.get("genres"))

        if data.get("tags"):
            self.tags.value = ", ".join(data.get("tags"))

        if data.get("complete"):
            self.complete = data.get("complete")

        self.arguments = data
        self.save()
    
    def save(self, *args, **kwargs):
        for field in self._meta.get_fields():
            if isinstance(field, OneToOneField):
                current_value = getattr(self, field.name)
                if current_value is None:
                    new_item = field.related_model.objects.create()
                    setattr(self, field.name, new_item)
        super().save(*args, **kwargs)

    def get_fields_values_for_xml(self) -> dict:
        return {
            "Series": self.name.value,
            "LocalizedSeries": self.localized_name.value,
            "Genre": self.genres.value,
            "Tags": self.tags.value,
            "Web": self.url,
        }

class MangaANLink(models.Model):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, related_name="alternative_names")
    alternative_names = models.OneToOneField(StringType, on_delete=models.PROTECT, verbose_name=_("database.models.manga.alternative_names"), related_name="manga_alternative_names")


class Volume(models.Model):
    name = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.volume.name"), related_name="volume_name")
    description = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.volume.description"), related_name="volume_description")
    number = models.OneToOneField(FloatType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.volume.number"), related_name="volume_number")
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, related_name="volumes")
    arguments = models.JSONField(default=dict, verbose_name=_("processes.models.volume.arguments"), blank=True)


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

    def update_fields(self, data:dict) -> None:            
        if data.get("name"):
            self.name.value = data.get("name")

        if data.get("description"):
            self.description.value = data.get("description")

        if data.get("volume_number"):
            self.number = data.get("volume_number")

        self.arguments = data
        self.save()

    def get_fields_values_for_xml(self) -> dict:
        return {
            **self.manga.get_fields_values_for_xml(),
            "Volume": self.volume,
        }

class Chapter(models.Model):
    name = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.name"), related_name="chapter_name")
    description = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.description"), related_name="chapter_description")
    localization = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.localization"), related_name="chapter_localization")
    publisher = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.publisher"), related_name="chapter_publisher")
    imprint = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.imprint"), related_name="chapter_imprint")
    release_date = models.OneToOneField(DateType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.release_date"), related_name="chapter_release_date")
    writer = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.writer"), related_name="chapter_writer")
    penciller = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.penciller"), related_name="chapter_penciller")
    inker = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.inker"), related_name="chapter_inker")
    colorist = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.colorist"), related_name="chapter_colorist")
    letterer = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.letterer"), related_name="chapter_letterer")
    cover_artist = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.cover_artist"), related_name="chapter_cover_artist")
    editor = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.editor"), related_name="chapter_editor")
    translator = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.translator"), related_name="chapter_translator")
    page_count = models.OneToOneField(IntType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.page_count"), related_name="chapter_page_count")
    format = models.OneToOneField(FormatsEnumType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.format"), related_name="chapter_format")
    age_rating = models.OneToOneField(AgeRatingEnumType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.age_rating"), related_name="chapter_age_rating")
    isbn = models.OneToOneField(StringType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.isbn"), related_name="chapter_isbn")
    number = models.OneToOneField(FloatType, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("database.models.chapter.number"), related_name="chapter_number")
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE, related_name="chapters")
    file = models.CharField(max_length=512, default=FILE_PATH_ROOT, verbose_name=_("database.models.chapter.file_path"))
    url = models.URLField(verbose_name=_("database.models.chapter.url"))
    source_url = models.URLField(verbose_name=_("database.models.chapter.source_url"))
    downloaded = models.BooleanField(default=False, verbose_name=_("database.models.chapter.downloaded"))
    arguments = models.JSONField(default=dict, verbose_name=_("processes.models.manga.arguments"), blank=True)


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

    def update_fields(self, data:dict) -> None:
        if data.get("name"):
            self.name.value = data.get("name")
            
        if data.get("description"):
            self.description.value = data.get("description")
            
        if data.get("localization"):
            self.localization.value = data.get("localization")
            
        if data.get("publisher"):
            self.publisher.value = data.get("publisher")
            
        if data.get("imprint"):
            self.imprint.value = data.get("imprint")
            
        if data.get("release_date"):
            self.release_date.value = data.get("release_date")
            
        if data.get("writer"):
            self.writer.value = data.get("writer")
            
        if data.get("penciller"):
            self.penciller.value = data.get("penciller")
            
        if data.get("inker"):
            self.inker.value = data.get("inker")
            
        if data.get("colorist"):
            self.colorist.value = data.get("colorist")
            
        if data.get("letterer"):
            self.letterer.value = data.get("letterer")
            
        if data.get("cover_artist"):
            self.cover_artist.value = data.get("cover_artist")
            
        if data.get("editor"):
            self.editor.value = data.get("editor")
            
        if data.get("translator"):
            self.translator.value = data.get("translator")
            
        if data.get("page_count"):
            self.page_count.value = data.get("page_count")
            
        if data.get("format"):
            self.format.value = Formats(data.get("format"))
            
        if data.get("age_rating"):
            self.age_rating.value = AgeRating(data.get("age_rating"))
            
        if data.get("isbn"):
            self.isbn.value = data.get("isbn")
            
        if data.get("chapter_number"):
            self.number.value = data.get("chapter_number")
            
        if data.get("source_url"):
            self.source_url = data.get("source_url")
            
        self.arguments = data
        self.save()

    def get_file_name(self) -> str:
        return make_valid_filename(f"{self.volume.manga.name.value} - Vol. {self.volume.volume} Ch. {self.chapter}.cbz")

    def get_fields_values_for_xml(self) -> dict:
        date = self.release_date.value
        return {
            **self.volume.get_fields_values_for_xml(),
            "Title": self.name.value,
            "Number": self.chapter,
            "Summary": self.description.value,
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
            "Format": "",
            "AgeRating": "",
            "GTIN": self.isbn.value,
        }

    def create_xml(self) -> str:
        root = ET.Element("ConicInfo")

        for tag, text in self.get_fields_values_for_xml().items():
            if text is None:
                continue
            ET.SubElement(root, tag).text = escape(str(text))

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