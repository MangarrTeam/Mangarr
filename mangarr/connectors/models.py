from polymorphic.models import PolymorphicModel
from django.db import models
from database.manga.utils import BaseModel
from database.manga.models import Library
from django.utils.translation import pgettext
from django.core.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)

# Create your models here.
class ConnectorBase(PolymorphicModel, BaseModel):
    name = "Connector"
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        verbose_name=pgettext("Library field name for connector", "database.models.library.name"),
        related_name="connectors"
    )

    class Meta:
        verbose_name = "Connector"
        verbose_name_plural = "Connectors"

    def clean(self):
        super().clean()
        if self.library:
            qs = self.__class__.objects.filter(library=self.library)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    'library': f"A {self.__class__.__name__} connector for this Library already exists."
                })
            
    def notify(self) -> bool:
        logger.warning(f"The connector {self.name} does not have notify function defined.")
        return False
    
    @property
    def parameters(self) -> dict:
        return {}

    @classmethod
    def get_available_connectors(cls):
        """Return all subclasses as (class_name, verbose_name) tuples."""
        subclasses = cls.__subclasses__()
        return [(sub.__name__.lower(), sub.__name__) for sub in subclasses]
    
    @classmethod
    def get_subclass_by_name(cls, name: str):
        for subclass in cls.__subclasses__():
            if subclass.__name__.lower() == name.lower():
                return subclass
        raise ValueError(f"No connector subclass found for '{name}'")
            
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Kavita(ConnectorBase):
    name = "Kavita"
    connector_library_id = models.CharField(max_length=32, verbose_name=pgettext("Library ID field name for Kavita", "database.models.connector.kavita.library_id"), unique=True)

    def __init__(self, *args, **kwargs):
        from .connectors.kavita import connector
        self.connector_class = connector
        super().__init__(*args, **kwargs)

    @property
    def parameters(self) -> dict:
        return {
            "Library ID": self.connector_library_id
        }
            
    def notify(self) -> bool:
        try:
            self.connector_class.notify(self.connector_library_id)
        except:
            return False
        return True