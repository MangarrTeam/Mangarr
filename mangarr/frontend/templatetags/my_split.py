from django import template

register = template.Library()

@register.filter
def my_split(value, delim):
    return value.split(delim)
