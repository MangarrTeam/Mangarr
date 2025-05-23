from django.db import models
from django.utils.translation import gettext_lazy as _
from abc import abstractmethod
from datetime import datetime
import time
import logging
logger = logging.getLogger(__name__)

STRING_DEFAULT = {"value": "", "locked": False}
BOOL_DEFAULT = {"value": False, "locked": False}
INT_DEFAULT = {"value": 0, "locked": False}
FLOAT_DEFAULT = {"value": 0.0, "locked": False}
DATE_DEFAULT = {"value": "1900-01-01T12:00:00+00:00", "locked": False}
ENUM_DEFAULT = {"value": 1, "locked": False}


def prevent_if_locked(func):
    def wrapper(self, new_value):
        if self.locked:
            logger.debug(f"{self._meta.model_name} tried to change its value but it is locked")
            return
        return func(self, new_value)
    return wrapper


class BaseType(models.Model):
    class Meta:
        abstract = True
    
    @property
    def value_str(self) -> str:
        return str(self.value)
    
    @property
    @abstractmethod
    def value(self) -> str:
        pass


class StringType(BaseType):
    _data = models.JSONField(default=dict, blank=True, verbose_name=_("database.data_types_models.data"))

    @property
    def value(self) -> str:
        return self._data.get("value", "")
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self._data["value"] = new_value
        self.save()

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **STRING_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        title = None

        for rel in self._meta.related_objects:
            if rel.one_to_one:
                accessor = rel.get_accessor_name()
                related_obj = getattr(self, accessor, None)
                if related_obj is not None:
                    title = f"{accessor} ({str(related_obj)})"

        return title or f"StringType: {self.pk}"

class BoolType(BaseType):
    _data = models.JSONField(default=dict, blank=True, verbose_name=_("database.data_types_models.data"))

    @property
    def value(self) -> str:
        return self._data.get("value", False)
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self._data["value"] = new_value
        self.save()

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **BOOL_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        title = None

        for rel in self._meta.related_objects:
            if rel.one_to_one:
                accessor = rel.get_accessor_name()
                related_obj = getattr(self, accessor, None)
                if related_obj is not None:
                    title = f"{accessor} ({str(related_obj)})"

        return title or f"BoolType: {self.pk}"


class IntType(BaseType):
    _data = models.JSONField(default=dict, blank=True, verbose_name=_("database.data_types_models.data"))

    @property
    def value(self) -> str:
        return self._data.get("value", 0)
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self._data["value"] = int(new_value)
        self.save()

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **INT_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        title = None

        for rel in self._meta.related_objects:
            if rel.one_to_one:
                accessor = rel.get_accessor_name()
                related_obj = getattr(self, accessor, None)
                if related_obj is not None:
                    title = f"{accessor} ({str(related_obj)})"

        return title or f"IntType: {self.pk}"


class FloatType(BaseType):
    _data = models.JSONField(default=dict, blank=True, verbose_name=_("database.data_types_models.data"))

    @property
    def value(self) -> str:
        return self._data.get("value", 0.0)
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self._data["value"] = float(new_value)
        self.save()

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **FLOAT_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        title = None

        for rel in self._meta.related_objects:
            if rel.one_to_one:
                accessor = rel.get_accessor_name()
                related_obj = getattr(self, accessor, None)
                if related_obj is not None:
                    title = f"{accessor} ({str(related_obj)})"

        return title or f"FloatType: {self.pk}"
    
class DateType(BaseType):
    _data = models.JSONField(default=dict, blank=True, verbose_name=_("database.data_types_models.data"))

    @property
    def value(self) -> datetime:
        return datetime.strptime(self._data.get("value", "1900-01-01T12:00:00+00:00"), "%Y-%m-%dT%H:%M:%S%z")
    
    @property
    def value_str(self) -> datetime:
        return self._data.get("value", "1900-01-01T12:00:00+00:00")
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        try:
            if type(new_value) == str:
                self._data["value"] = datetime.strptime(new_value, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%dT%H:%M:%S%z")
            if type(new_value) == datetime:
                self._data["value"] = new_value.strftime("%Y-%m-%dT%H:%M:%S%z")
        except Exception as e:
            logger.error(f"Error - {e}")
        else:
            self.save()

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **DATE_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        title = None

        for rel in self._meta.related_objects:
            if rel.one_to_one:
                accessor = rel.get_accessor_name()
                related_obj = getattr(self, accessor, None)
                if related_obj is not None:
                    title = f"{accessor} ({str(related_obj)})"

        return title or f"DateType: {self.pk}"
    
from plugins.base import Formats, AgeRating, Status
    
class FormatsEnumType(BaseType):
    _data = models.JSONField(default=dict, blank=True, verbose_name=_("database.data_types_models.data"))

    @property
    def value(self) -> Formats:
        return Formats(self._data["value"])
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value:Formats) -> None:
        self._data["value"] = new_value.value
        self.save()

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **ENUM_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        title = None

        for rel in self._meta.related_objects:
            if rel.one_to_one:
                accessor = rel.get_accessor_name()
                related_obj = getattr(self, accessor, None)
                if related_obj is not None:
                    title = f"{accessor} ({str(related_obj)})"

        return title or f"FormatsEnumType: {self.pk}"
    
class AgeRatingEnumType(BaseType):
    _data = models.JSONField(default=dict, blank=True, verbose_name=_("database.data_types_models.data"))

    @property
    def value(self) -> AgeRating:
        return AgeRating(self._data["value"])
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value:AgeRating) -> None:
        self._data["value"] = new_value.value
        self.save()

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **ENUM_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        title = None

        for rel in self._meta.related_objects:
            if rel.one_to_one:
                accessor = rel.get_accessor_name()
                related_obj = getattr(self, accessor, None)
                if related_obj is not None:
                    title = f"{accessor} ({str(related_obj)})"

        return title or f"AgeRatingEnumType: {self.pk}"
    
class StatusEnumType(BaseType):
    _data = models.JSONField(default=dict, blank=True, verbose_name=_("database.data_types_models.data"))

    @property
    def value(self) -> Status:
        return Status(self._data["value"])
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value:Status) -> None:
        self._data["value"] = new_value.value
        self.save()

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **ENUM_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        title = None

        for rel in self._meta.related_objects:
            if rel.one_to_one:
                accessor = rel.get_accessor_name()
                related_obj = getattr(self, accessor, None)
                if related_obj is not None:
                    title = f"{accessor} ({str(related_obj)})"

        return title or f"StatusEnumType: {self.pk}"