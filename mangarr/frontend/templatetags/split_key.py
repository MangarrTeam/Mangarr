from django import template

register = template.Library()

@register.filter
def split_key(value):
    return value.replace('_', ' ')
