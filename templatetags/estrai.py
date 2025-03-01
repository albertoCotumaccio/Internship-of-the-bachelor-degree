from django import template

register = template.Library()

@register.filter
def estrai(value,pos):
    return value[pos]