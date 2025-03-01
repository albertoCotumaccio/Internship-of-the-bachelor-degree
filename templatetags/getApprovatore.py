from django import template
from app.models import MenuSettimana, User

register = template.Library()

@register.filter
def getApprovatore(menuSettimana):
    ins = []
    for menu in menuSettimana:
        ins.append(menu.approvatore)
    if None in ins:
        return ""
    return ins[0].first_name +" " +ins[0].last_name
