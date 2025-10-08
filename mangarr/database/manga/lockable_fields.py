from django.db import models
from django.core.exceptions import ValidationError

class LockableFieldBase(models.JSONField):
    """
    Base class for lockable fields. Stores data in JSON format with 'value' and 'locked' keys.
    """
    
    def __init__(self, *args, **kwargs):
        # Set default value structure
        kwargs.setdefault('default', self.get_default_structure)
        super().__init__(*args, **kwargs)
    
    def get_default_structure(self):
        """Returns the default structure for the lockable field."""
        return {
            'value': self.get_default_value(),
            'locked': False
        }
    
    def get_default_value(self):
        """Override this method in subclasses to provide type-specific defaults."""
        return None
    
    def get_prep_value(self, value):
        """Convert the value to a format suitable for the database."""
        # If it's a LockableFieldProxy, get the raw data
        if isinstance(value, LockableFieldProxy):
            value = value._get_data()
        # If it's already a dict, use it as-is
        elif not isinstance(value, dict):
            # If it's some other value, wrap it in our structure
            value = {'value': value, 'locked': False}
        return super().get_prep_value(value)
    
    def from_db_value(self, value, expression, connection):
        """Convert the database value to a Python object."""
        if value is None:
            return self.get_default_structure()
        
        # Django's JSONField should already parse JSON, but handle string edge case
        if isinstance(value, str):
            import json
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {'value': value, 'locked': False}
        
        # Ensure it has the correct structure
        if isinstance(value, dict) and 'value' in value and 'locked' in value:
            return value
        
        # If it doesn't have the right structure, wrap it
        return {'value': value, 'locked': False}
    
    def value_from_object(self, obj):
        """Get the value from a model instance for forms/admin."""
        value = super().value_from_object(obj)
        # If it's a LockableFieldProxy, get the raw data
        if isinstance(value, LockableFieldProxy):
            return value._get_data()
        return value
    
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Remove default from kwargs as we handle it in __init__
        if 'default' in kwargs and kwargs['default'] == self.get_default_structure:
            del kwargs['default']
        return name, path, args, kwargs


class LockableFieldDescriptor:
    """
    Descriptor that provides a convenient interface for lockable fields.
    """
    
    def __init__(self, field_name, value_type=None, validator=None, enum_class=None):
        self.field_name = field_name
        self.attname = field_name
        self.value_type = value_type
        self.validator = validator
        self.enum_class = enum_class
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return LockableFieldProxy(instance, self.attname, self.value_type, self.validator, self.enum_class)
    
    def __set__(self, instance, value):
        # If value is already a dict with 'value' and 'locked', set it directly
        if isinstance(value, dict) and 'value' in value and 'locked' in value:
            instance.__dict__[self.attname] = value
        else:
            # Otherwise, treat it as a value to be set
            proxy = self.__get__(instance, type(instance))
            proxy.set_value(value, force=False)


class LockableFieldProxy:
    """
    Proxy object that provides the interface for interacting with lockable fields.
    """
    
    def __init__(self, instance, field_name, value_type=None, validator=None, enum_class=None):
        self._instance = instance
        self._field_name = field_name
        self._value_type = value_type
        self._validator = validator
        self._enum_class = enum_class
    
    def _get_data(self):
        """Get the raw data dictionary from the model instance."""
        # Access the actual field data directly from __dict__ to avoid descriptor recursion
        data = self._instance.__dict__.get(self._field_name)
        if not isinstance(data, dict) or 'value' not in data or 'locked' not in data:
            # Get the field to access its default value
            field = self._instance._meta.get_field(self._field_name)
            default_value = field.get_default_value() if hasattr(field, 'get_default_value') else None
            data = {'value': default_value, 'locked': False}
            # Write directly to __dict__ to bypass descriptor
            self._instance.__dict__[self._field_name] = data
        return data
    
    def _set_data(self, data):
        """Set the raw data dictionary to the model instance."""
        # Write directly to __dict__ to bypass descriptor
        self._instance.__dict__[self._field_name] = data
    
    @property
    def value(self):
        """Get the current value."""
        data = self._get_data()
        return data.get('value')
    
    @value.setter
    def value(self, new_value):
        """Set the value. Raises ValidationError if locked."""
        self.set_value(new_value, force=False)
    
    def set_value(self, new_value, force=False):
        """
        Set the value of the field.
        
        Args:
            new_value: The new value to set
            force: If True, bypass the lock check
        
        Raises:
            ValidationError: If the field is locked and force=False
        """
        data = self._get_data()
        
        if data.get('locked', False) and not force:
            raise ValidationError(f"Field '{self._field_name}' is locked and cannot be modified.")
        
        # Validate and convert type if specified
        if self._validator:
            new_value = self._validator(new_value)
        elif self._value_type and new_value is not None:
            try:
                new_value = self._value_type(new_value)
            except (ValueError, TypeError) as e:
                raise ValidationError(f"Invalid value type for '{self._field_name}': {e}")
        
        data['value'] = new_value
        self._set_data(data)
    
    def lock(self):
        """Lock the field to prevent modifications."""
        data = self._get_data()
        data['locked'] = True
        self._set_data(data)
    
    def unlock(self):
        """Unlock the field to allow modifications."""
        data = self._get_data()
        data['locked'] = False
        self._set_data(data)
    
    @property
    def locked(self):
        """Get the current lock state."""
        data = self._get_data()
        return data.get('locked', False)
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return f"<LockableFieldProxy: value={self.value}, locked={self.locked}>"
    
    # Comparison methods for enum support
    def __eq__(self, other):
        """Enable comparison with enum values."""
        value = self.value
        
        # If this is an enum field, compare with enum members
        if self._enum_class:
            # If comparing with an enum instance
            if isinstance(other, self._enum_class):
                return value == other.value
            # If comparing with enum value directly
            for enum_member in self._enum_class:
                if other == enum_member.value or other == enum_member:
                    return value == enum_member.value
        
        # Default comparison
        return value == other
    
    def __ne__(self, other):
        """Enable not-equal comparison."""
        return not self.__eq__(other)
    
    def __hash__(self):
        """Make the proxy hashable."""
        return hash(self.value)


class LockableCharField(LockableFieldBase):
    """
    Lockable field for string values.
    """
    def __init__(self, default=None, *args, **kwargs):
        self._default = default
        super().__init__(*args, **kwargs)
    
    def get_default_value(self):
        return self._default or ""
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Store the actual field name (attname) for direct access
        descriptor = LockableFieldDescriptor(self.attname, value_type=str)
        setattr(cls, name, descriptor)


class LockableListField(LockableFieldBase):
    """
    Lockable field for list values.
    """
    def __init__(self, default=None, *args, **kwargs):
        self._default = default
        super().__init__(*args, **kwargs)
    
    def get_default_value(self):
        return self._default or []
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Store the actual field name (attname) for direct access
        descriptor = LockableFieldDescriptor(self.attname, value_type=list)
        setattr(cls, name, descriptor)


class LockableBoolField(LockableFieldBase):
    """
    Lockable field for boolean values.
    """
    def __init__(self, default=None, *args, **kwargs):
        self._default = default
        super().__init__(*args, **kwargs)
    
    def get_default_value(self):
        return self._default or False
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Store the actual field name (attname) for direct access
        descriptor = LockableFieldDescriptor(self.attname, value_type=bool)
        setattr(cls, name, descriptor)


class LockableIntegerField(LockableFieldBase):
    """
    Lockable field for integer values.
    """
    def __init__(self, default=None, *args, **kwargs):
        self._default = default
        super().__init__(*args, **kwargs)
    
    def get_default_value(self):
        return self._default or 0
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Store the actual field name (attname) for direct access
        descriptor = LockableFieldDescriptor(self.attname, value_type=int)
        setattr(cls, name, descriptor)


class LockableFloatField(LockableFieldBase):
    """
    Lockable field for integer values.
    """
    def __init__(self, default=None, *args, **kwargs):
        self._default = default
        super().__init__(*args, **kwargs)
    
    def get_default_value(self):
        return self._default or 0.0
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Store the actual field name (attname) for direct access
        descriptor = LockableFieldDescriptor(self.attname, value_type=float)
        setattr(cls, name, descriptor)


class LockableDateTimeField(LockableFieldBase):
    """
    Lockable field for datetime values.
    """
    def __init__(self, default=None, *args, **kwargs):
        self._default = default
        super().__init__(*args, **kwargs)
    
    def get_default_value(self):
        from datetime import datetime, timezone
        return self._default or datetime(1900, 1, 1, 12, 0, tzinfo=timezone.utc)
    
    def from_db_value(self, value, expression, connection):
        """Convert the database value to a Python object, converting enum values back to enum instances."""
        result = super().from_db_value(value, expression, connection)
        
        # Convert the stored value back to an enum instance
        if isinstance(result, dict) and result.get('value') is not None:
            stored_value = result['value']
            # Try to convert the stored value back to the enum instance
            try:
                from datetime import datetime
                result['value'] = datetime.fromisoformat(stored_value)
            except Exception:
                pass  # Keep the raw value if conversion fails
        
        return result
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        
        def datetime_validator(value):
            """Validate and convert datetime values."""
            if value is None:
                return None
            
            from datetime import datetime
            import django.utils.timezone as timezone
            
            # If it's already a datetime, return it
            if isinstance(value, datetime):
                return value
            
            # If it's a string, try to parse it
            if isinstance(value, str):
                try:
                    # Try parsing ISO format
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    # Make it timezone-aware if settings.USE_TZ is True
                    if timezone.is_naive(dt) and getattr(django.conf.settings, 'USE_TZ', False):
                        dt = timezone.make_aware(dt)
                    return dt
                except (ValueError, AttributeError):
                    raise ValidationError(f"Invalid datetime format: {value}")
            
            raise ValidationError(f"Cannot convert {type(value).__name__} to datetime")
        
        descriptor = LockableFieldDescriptor(self.attname, validator=datetime_validator)
        setattr(cls, name, descriptor)
    
    def get_prep_value(self, value):
        """Convert the value to a format suitable for the database."""
        # If it's a LockableFieldProxy, get the raw data
        if isinstance(value, LockableFieldProxy):
            data = value._get_data()
            # Convert datetime to ISO string for JSON serialization
            if data.get('value') is not None:
                from datetime import datetime
                if isinstance(data['value'], datetime):
                    data = data.copy()
                    data['value'] = data['value'].isoformat()
            value = data
        elif isinstance(value, dict):
            # Handle datetime in dict
            if value.get('value') is not None:
                from datetime import datetime
                if isinstance(value['value'], datetime):
                    value = value.copy()
                    value['value'] = value['value'].isoformat()
        
        return super().get_prep_value(value)


class LockableEnumField(LockableFieldBase):
    """
    Lockable field for Enum values.
    """
    
    def __init__(self, default=None, enum_class=None, *args, **kwargs):
        self._default = default
        self.enum_class = enum_class
        if enum_class is None:
            raise ValueError("enum_class is required for LockableEnumField")
        super().__init__(*args, **kwargs)
    
    def get_default_value(self):
        if self.enum_class:
            return (self._default.value if self._default else None) or list(self.enum_class)[0].value
        return (self._default.value if self._default else None) or None
    
    def get_value_formfield(self):
        """Return a select dropdown for enum values."""
        choices = [(e.value, e.label if hasattr(e, 'label') and e.label else e.name.replace('_', ' ').title()) for e in self.enum_class]
        return forms.ChoiceField(
            required=False, 
            label="Value",
            choices=choices,
            widget=forms.Select(attrs={'class': 'vSelectField'})
        )
    
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        
        enum_class = self.enum_class
        
        def enum_validator(value):
            """Validate and convert enum values to enum instances."""
            if value is None:
                return None
            
            # If it's already an enum instance, return it as-is
            if isinstance(value, enum_class):
                return value
            
            # If it's a value or name, convert to enum instance
            for enum_member in enum_class:
                if value == enum_member.value or value == enum_member.name:
                    return enum_member  # Return the enum instance, not the value
            
            # If we get here, the value is invalid
            valid_values = [e.value for e in enum_class]
            raise ValidationError(
                f"Invalid enum value: {value}. Valid values are: {valid_values}"
            )
        
        descriptor = LockableFieldDescriptor(self.attname, validator=enum_validator, enum_class=enum_class)
        setattr(cls, name, descriptor)
    
    def from_db_value(self, value, expression, connection):
        """Convert the database value to a Python object, converting enum values back to enum instances."""
        result = super().from_db_value(value, expression, connection)
        
        # Convert the stored value back to an enum instance
        if isinstance(result, dict) and result.get('value') is not None:
            stored_value = result['value']
            # Try to convert the stored value back to the enum instance
            try:
                for enum_member in self.enum_class:
                    if stored_value == enum_member.value:
                        result['value'] = enum_member
                        break
            except Exception:
                pass  # Keep the raw value if conversion fails
        
        return result
    
    def get_prep_value(self, value):
        """Convert the value to a format suitable for the database."""
        # If it's a LockableFieldProxy, get the raw data
        if isinstance(value, LockableFieldProxy):
            data = value._get_data()
            # Convert enum instance to its value
            if data.get('value') is not None:
                val = data['value']
                if isinstance(val, self.enum_class):
                    data = data.copy()
                    data['value'] = val.value
            value = data
        elif isinstance(value, dict):
            # Handle enum in dict
            if value.get('value') is not None:
                val = value['value']
                if isinstance(val, self.enum_class):
                    value = value.copy()
                    value['value'] = val.value
        
        return super().get_prep_value(value)
    
    def to_python(self, value):
        """Convert the value to Python object, converting enum values back to enum instances."""
        result = super().to_python(value)
        
        # Convert the stored value back to an enum instance
        if isinstance(result, dict) and result.get('value') is not None:
            stored_value = result['value']
            # Try to convert the stored value back to the enum instance
            if not isinstance(stored_value, self.enum_class):
                try:
                    for enum_member in self.enum_class:
                        if stored_value == enum_member.value:
                            result['value'] = enum_member
                            break
                except Exception:
                    pass  # Keep the raw value if conversion fails
        
        return result
    
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['enum_class'] = self.enum_class
        return name, path, args, kwargs