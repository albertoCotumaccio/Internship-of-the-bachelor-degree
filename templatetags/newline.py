from django import template

register = template.Library()

@register.filter
def newline(stringa):
    text = ""
    frasi = stringa.split("\n")
    frasi.pop()
    return frasi

#crea una lista e toglie l'ultimo elemento perche è un ""