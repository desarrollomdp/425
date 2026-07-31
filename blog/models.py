from django.db import models
from django.contrib.auth.models import User

# models.py
class Post(models.Model):
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    imagen1 = models.ImageField(upload_to='blog/', blank=True, null=True)
    imagen2 = models.ImageField(upload_to='blog/', blank=True, null=True)
    imagen3 = models.ImageField(upload_to='blog/', blank=True, null=True)
    imagen4 = models.ImageField(upload_to='blog/', blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def imagenes(self):
        return [img for img in [self.imagen1, self.imagen2, self.imagen3, self.imagen4] if img]


class Comentario(models.Model):
    post = models.ForeignKey(Post, related_name='comentarios', on_delete=models.CASCADE)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comentario de {self.autor.username} en {self.post.id}'


class Reaccion(models.Model):
    TIPOS_REACCION = (
        ('like', 'Me gusta'),
        ('love', 'Me encanta'),
        ('wow', 'Sorprendido'),
        ('sad', 'Triste'),
        ('angry', 'Enojado'),
    )

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reacciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPOS_REACCION)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'usuario')

    def __str__(self):
        return f"{self.usuario.username} reaccionó con {self.tipo}"
