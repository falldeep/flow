from django.template import Library
from web import models
from django.shortcuts import  reverse

register = Library()

@register.simple_tag
@register.simple_tag
def use_space(size):
    if size > 1024 * 1024 * 1024:
        return "%.2f GB" % (size / (1024 * 1024 * 1024))
    elif size >= 1024 * 1024:
        return "%.2f MB" % (size / (1024 * 1024))
    elif size >= 1024:
        return "%d KB" % (size / 1024)
    return "%d B" % size