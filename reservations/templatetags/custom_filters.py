from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Sépare une chaîne selon un délimiteur"""
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter)]

@register.filter
def trim(value):
    """Supprime les espaces en début et fin"""
    return value.strip() if value else value