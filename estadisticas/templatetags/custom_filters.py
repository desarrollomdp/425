from django import template

register = template.Library()

@register.filter
def zip_lists(list1, list2):
    return zip(list1, list2)
from django import template

register = template.Library()

@register.filter
def dict_item(dictionary, key):
    return dictionary.get(key, 'N/A')  # Devuelve 'N/A' si la clave no se encuentra
