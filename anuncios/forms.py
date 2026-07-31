from django import forms
from .models import Anuncio
from django.forms import DateInput

class AnuncioForm(forms.ModelForm):
    class Meta:
        model = Anuncio
        fields = [
            'titulo', 'imagen_desktop', 'imagen_movil',
            'texto_promocional', 'url_destino', 'mensaje_predefinido',
            'whatsapp', 'activo', 'fecha_inicio', 'fecha_fin', 'prioridad',
            'mostrar_una_vez_por_dia'
        ]
        widgets = {
            'fecha_inicio': DateInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'fecha_fin': DateInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'mensaje_predefinido': forms.Textarea(attrs={'rows': 3}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del anuncio'}),
            'texto_promocional': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto corto (max 200)'}),
            'url_destino': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1122334455 (10 dígitos)'}),
            'prioridad': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'imagen_desktop': 'Imagen Desktop (Obligatorio)',
            'imagen_movil': 'Imagen Móvil (Opcional)',
            'mensaje_predefinido': 'Mensaje Predefinido para WhatsApp',
            'mostrar_una_vez_por_dia': 'Mostrar solo una vez al día por usuario'
        }
