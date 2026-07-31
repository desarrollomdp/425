# cuentas/storage_backends.py

import os
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class HybridMediaStorage(S3Boto3Storage):
    """
    Este storage intenta servir el archivo desde el disco local primero.
    Si no existe localmente, asume que está en R2/S3 y devuelve esa URL.
    Para guardar (upload), siempre usa la configuración de S3/R2 heredada.
    """
    
    location = 'media'
    file_overwrite = False

    def url(self, name):
        # 1. Construir la ruta física completa en el VPS
        # Limpiamos el nombre por si viene con 'media/' duplicado
        clean_name = name.replace('media/', '') 
        local_path = os.path.join(settings.MEDIA_ROOT, clean_name)

        # 2. Verificar si el archivo existe físicamente en el VPS
        if os.path.exists(local_path):
            # Si existe local, devolvemos la URL local (/media/archivo.jpg)
            return settings.MEDIA_URL + clean_name
        
        # 3. Si no existe local, devolvemos la URL de R2 (comportamiento normal)
        return super().url(name)