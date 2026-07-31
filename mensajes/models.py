
# mensajes/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

def validar_peso_archivo(archivo):
    limite_mb = 10
    if archivo.size > limite_mb * 1024 * 1024:
        raise ValidationError(f"El archivo es muy pesado. Capacidad máxima {limite_mb} MB.")

class Mensaje_socket(models.Model):
    emisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='socket_enviados')
    receptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='socket_recibidos')
    contenido = models.TextField(blank=True, null=True)
    archivo = models.FileField(upload_to='chat_archivos/%Y/%m/%d/', validators=[validar_peso_archivo], blank=True, null=True)
    es_imagen = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.archivo and not self.es_imagen:
            nombre_ext = os.path.splitext(self.archivo.name)[1].lower()
            print(nombre_ext)
            if nombre_ext in ['.jpg', '.jpeg', '.png']:
                # Optimización a WebP
                img = Image.open(self.archivo)
                output = BytesIO()
                # Convertimos a RGB si es necesario (para evitar errores con transparencias en JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
            
                img.save(output, format='WebP', quality=70) # Calidad 70 es el punto dulce
                output.seek(0)
            
                # Cambiamos el nombre del archivo a .webp
                nuevo_nombre = os.path.splitext(self.archivo.name)[0] + ".webp"
                self.archivo = ContentFile(output.read(), name=nuevo_nombre)
                self.es_imagen = True
            
        super().save(*args, **kwargs)
    def __str__(self):
        return f"De {self.emisor} para {self.receptor}"