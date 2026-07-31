from django import forms
from .models import Post,Comentario

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['texto', 'imagen1', 'imagen2', 'imagen3', 'imagen4']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 4, 'placeholder': '¿Qué estás pensando?'}),
        }


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Escribe un comentario...'}),
        }
