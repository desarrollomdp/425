from django.db import models
from cursos.models import Curso

class Inscripcion(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    celular = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    edad = models.IntegerField()
    cursos = models.ManyToManyField(Curso)  # Usar ManyToManyField para cursos

    def __str__(self):
        # Obtener nombres de los cursos seleccionados
        cursos_nombres = ', '.join([curso.nombre for curso in self.cursos.all()])
        return f"{self.nombre} {self.apellido} - Cursos: {cursos_nombres}"
