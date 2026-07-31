from django import template
from django.conf import settings
import os

register = template.Library()

@register.filter
def safe_file_url(file_field):
    """
    Retorna la URL correcta del archivo, manejando tanto archivos en media local como en R2.
    Si el archivo no existe, retorna None.
    """
    if not file_field:
        return None
    
    try:
        # Intentar obtener el path del archivo
        file_path = file_field.name
        
        # Verificar si existe en media local
        local_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        if os.path.exists(local_path):
            # Archivo existe en local, usar URL de media local
            return settings.MEDIA_URL + file_path
        else:
            # Archivo probablemente está en R2, usar la URL del storage
            return file_field.url
    except (ValueError, AttributeError):
        # Si hay algún error, retornar None
        return None
