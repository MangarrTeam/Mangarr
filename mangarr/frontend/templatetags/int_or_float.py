from django import template

register = template.Library()

@register.filter
def int_or_float(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value
