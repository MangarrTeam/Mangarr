from django import template
from django.urls import reverse

register = template.Library()

@register.filter
def my_reverse(value):
    return reverse(value)
