from django import template
from django.urls import reverse

register = template.Library()

@register.filter
def get_full_uri(request, path):
    return request.build_absolute_uri(reverse(path))
