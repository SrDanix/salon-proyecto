from django import template

register = template.Library()

@register.filter
def precio_cl(valor):
    try:
        valor = int(valor)
        return f"{valor:,}".replace(",", ".").replace(" ", ".")
    except:
        return valor
