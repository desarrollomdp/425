from django.contrib import admin

# Register your models here.
from .models import Comentario, Post
admin.site.register(Post)

admin.site.register(Comentario)
