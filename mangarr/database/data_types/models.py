from django.db import models
from django.utils.translation import pgettext
from abc import abstractmethod
from datetime import datetime
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
    _data = models.JSONField(default=dict, blank=True, verbose_name=pgettext("Data field name for Type models", "database.data_types.models.data"))

    class Meta:
        abstract = True
    
    @property
    def value_str(self) -> str:
        return str(self.value)
    
    @property
    @abstractmethod
    def value(self) -> str:
        pass

    @property
    def locked(self) -> bool:
        return self._data.get("locked", False)
    
    def lock(self):
        self._data["locked"] = True
        self.save()

    def unlock(self):
        self._data["locked"] = False
        self.save()

    def __str__(self) -> str:
        v = f"{self.value}"[:50]
        if len(v) == 0:
            return f"{self.__class__.__name__}: {self.pk} [{"Locked" if self.locked else "Not locked"}]"
        return f"{self.__class__.__name__}: {self.pk} ({v}) [{"Locked" if self.locked else "Not locked"}]"


class StringType(BaseType):
    @property
    def value(self) -> str:
        return self._data.get("value", "")
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self.value_force(new_value)
    
    def value_force(self, new_value) -> None:
        if self.value == new_value:
            return
        self._data["value"] = new_value
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **STRING_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

class BoolType(BaseType):
    @property
    def value(self) -> str:
        return self._data.get("value", False)
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self.value_force(new_value)
    
    def value_force(self, new_value) -> None:
        if self.value == new_value:
            return
        self._data["value"] = new_value
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **BOOL_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

class IntType(BaseType):
    @property
    def value(self) -> str:
        return self._data.get("value", 0)
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self.value_force(new_value)
    
    def value_force(self, new_value) -> None:
        if self.value == int(new_value):
            return
        self._data["value"] = int(new_value)
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **INT_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

class FloatType(BaseType):
    @property
    def value(self) -> str:
        return self._data.get("value", 0.0)
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self.value_force(new_value)
    
    def value_force(self, new_value) -> None:
        if self.value == float(new_value):
            return
        self._data["value"] = float(new_value)
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **FLOAT_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

from server.settings import DATETIME_FORMAT
    
class DateType(BaseType):
    @property
    def value(self) -> datetime:
        return datetime.strptime(self._data.get("value", "1900-01-01T12:00:00+00:00"), DATETIME_FORMAT)
    
    @property
    def value_str(self) -> datetime:
        return self._data.get("value", "1900-01-01T12:00:00+00:00")
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value) -> None:
        self.value_force(new_value)
    
    def value_force(self, new_value) -> None:
        try:
            if type(new_value) == str:
                d = datetime.strptime(new_value, DATETIME_FORMAT).strftime(DATETIME_FORMAT)
                if self.value == d:
                    return
                self._data["value"] = d
            if type(new_value) == datetime:
                d = new_value.strftime(DATETIME_FORMAT)
                if self.value == d:
                    return
                self._data["value"] = d
        except Exception as e:
            logger.error(f"Error - {e}")
        else:
            self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **DATE_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

from plugins.base import Formats, AgeRating, Status
    
class FormatsEnumType(BaseType):
    @property
    def value(self) -> Formats:
        return Formats(self._data["value"])
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value:Formats) -> None:
        self.value_force(new_value)
    
    def value_force(self, new_value:Formats) -> None:
        if self.value == new_value.value:
            return
        self._data["value"] = new_value.value
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **ENUM_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

class AgeRatingEnumType(BaseType):
    @property
    def value(self) -> AgeRating:
        return AgeRating(self._data["value"])
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value:AgeRating) -> None:
        self.value_force(new_value)
    
    def value_force(self, new_value:AgeRating) -> None:
        if self.value == new_value.value:
            return
        self._data["value"] = new_value.value
        self.save()

    def save(self, *args, **kwargs):
        self._data = {
            **ENUM_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)

class StatusEnumType(BaseType):
    @property
    def value(self) -> Status:
        return Status(self._data["value"])
    
    @value.setter
    @prevent_if_locked
    def value(self, new_value:Status) -> None:
        if self.value == new_value.value:
            return
        self._data["value"] = new_value.value
        self.save()
    
    def value_force(self, new_value:Status) -> None:
        self.value_force(new_value)

    def save(self, *args, **kwargs):
        self._data = {
            **ENUM_DEFAULT,
            **self._data
        }
        super().save(*args, **kwargs)