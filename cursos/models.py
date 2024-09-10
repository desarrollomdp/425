from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    imagen_url = models.URLField(max_length=500, blank=True)  # Campo de texto para la URL de la imagen
    def __str__(self):
        return self.nombre
