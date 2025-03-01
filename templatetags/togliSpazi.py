from django import template

register = template.Library()


@register.filter(name='togli_spazi')
def togli_spazi(stringa):
    stringa= stringa.replace(" ", "-") #tolgo spazi
    return stringa.replace(".", "-")    #tolgo punti