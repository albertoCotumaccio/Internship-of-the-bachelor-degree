from django import template
from app.models import Area,Impianto, CapoArea,User,Chef

register = template.Library()


@register.filter
def getRuoloUser(user):
    if user.is_staff:
        return "Utente direzionale"
    try:
        chef = Chef.objects.get(user=user)
        if chef.manager:
            return "Chef: " + chef.impianto.nome + " - Manager"
        else:
            return "Chef: " + chef.impianto.nome
    except Chef.DoesNotExist:
        try:
            area = Area.objects.get(capo= CapoArea.objects.get(user=user) )
            return "Capo area: " + area.nome
        except:
            return "Capo area: da definire"
    return ""