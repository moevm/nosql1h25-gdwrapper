from django import template

register = template.Library()

@register.filter
def get_items(dictionary, key):
    return dictionary.get(key, [])