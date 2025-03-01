from django import template
from app.models import Tag,MenuSettimana,Ricetta

register = template.Library()

@register.filter
def toListOrdinata(ricette):
    tags = Tag.objects.all().order_by('posizione')
    ricetteGiorno = []
    for tag in tags:
        for ricetta in ricette:
            if ricetta.tag == tag:
                ricetteGiorno.append(ricetta)
    return ricetteGiorno
#prende in input le ricette di un menu giornaliero e ritorna la lista ordinata per posizione dei tag