from django.contrib import admin
from .models import Anuncio
from .models import Anuncio, ImpresionAnuncio, ClickAnuncio

@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display = ("titulo", "activo", "esta_vigente", "whatsapp", "fecha_inicio", "fecha_fin", "prioridad")
    list_filter = ("activo",)
    search_fields = ("titulo", "texto_promocional", "whatsapp", "mensaje_predefinido")
    fieldsets = (
        (None, {
            'fields': ('titulo', 'texto_promocional', 'activo', 'prioridad')
        }),
        ('Imágenes', {
            'fields': ('imagen_desktop', 'imagen_movil')
        }),
        ('Enlaces y mensajes', {
            'fields': ('url_destino', 'whatsapp', 'mensaje_predefinido')
        }),
        ('Programación', {
            'fields': ('fecha_inicio', 'fecha_fin', 'mostrar_una_vez_por_dia')
        }),
    )






@admin.register(ImpresionAnuncio)
class ImpresionAdmin(admin.ModelAdmin):
    list_display = ('anuncio', 'usuario', 'timestamp', 'ip')
    list_filter = ('anuncio',)
    date_hierarchy = 'timestamp'
    search_fields = ('usuario__username', 'ip', 'user_agent')

@admin.register(ClickAnuncio)
class ClickAdmin(admin.ModelAdmin):
    list_display = ('anuncio', 'usuario', 'timestamp', 'ip')
    list_filter = ('anuncio',)
    date_hierarchy = 'timestamp'
    search_fields = ('usuario__username', 'ip', 'user_agent')
