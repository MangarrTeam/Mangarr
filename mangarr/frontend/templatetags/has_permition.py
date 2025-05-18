from django import template

register = template.Library()

@register.filter
def has_permition(user, perm):
    return user.has_perm(perm)
