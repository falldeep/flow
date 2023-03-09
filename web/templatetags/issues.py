from django.template import Library
from web import models
from django.shortcuts import  reverse

register = Library()

@register.simple_tag
def number(num):
    if num < 100:
        num = str(num).rjust(3,"0")
    return "#{}".format(num)