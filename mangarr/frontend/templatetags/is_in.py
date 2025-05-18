from django import template

register = template.Library()

@register.filter
def is_in(value, arg):
    return value in arg.split(",")
