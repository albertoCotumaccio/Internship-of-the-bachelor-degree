from django import template
from app.models import Area,Impianto, CapoArea,User,Chef

register = template.Library()


@register.filter
def getImpiantiTab(user):
    impiantiTab = dict()
    if user.is_staff:
        aree = Area.objects.all()
        for area in aree:
            impiantiTab[area] = Impianto.objects.filter(area=area)
    else:
        try:
            impianto = Chef.objects.get(user = user).impianto
            impiantiTab[impianto.area] = [impianto]
        except Chef.DoesNotExist:
            area = Area.objects.get(capo__user = user)
            impiantiTab[area] = Impianto.objects.filter(area=area)
    return impiantiTab.items()