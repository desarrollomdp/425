import re
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings

class Anuncio(models.Model):
    titulo = models.CharField(max_length=120)
    imagen_desktop = models.ImageField(upload_to='anuncios/desktop/')
    imagen_movil = models.ImageField(upload_to='anuncios/movil/', blank=True, null=True)

    texto_promocional = models.CharField(max_length=200, blank=True, null=True)
    url_destino = models.URLField(blank=True, null=True)
    mensaje_predefinido = models.TextField(
        blank=True, 
        null=True,
        help_text="Mensaje que se enviará automáticamente cuando el usuario haga clic en la imagen"
    )

    # 🔹 NUEVO: WhatsApp solo 10 dígitos, ej. 1122334455
    whatsapp = models.CharField(
        max_length=10, blank=True, null=True,
        validators=[RegexValidator(r'^\d{10}$', message="Usá 10 dígitos: 1122334455")]
    )

    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    prioridad = models.PositiveIntegerField(default=10)
    mostrar_una_vez_por_dia = models.BooleanField(default=True)

    class Meta:
        ordering = ["prioridad", "-fecha_inicio"]

    def __str__(self):
        return self.titulo

    @property
    def esta_vigente(self):
        ahora = timezone.now()
        if self.fecha_fin and ahora > self.fecha_fin:
            return False
        return self.activo and self.fecha_inicio <= ahora

    # 🔹 NUEVO: link automático a WhatsApp (Argentina por defecto: 54)
    @property
    def whatsapp_link(self) -> str | None:
        if not self.whatsapp:
            return None
        numero = re.sub(r'\D+', '', self.whatsapp)  # por si acaso
        base_url = f"https://wa.me/54{numero}"
        if self.mensaje_predefinido:
            from urllib.parse import quote
            mensaje_codificado = quote(self.mensaje_predefinido)
            return f"{base_url}?text={mensaje_codificado}"
        return base_url


class ImpresionAnuncio(models.Model):
    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name='impresiones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='impresiones_anuncio')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['anuncio', 'timestamp']),
            models.Index(fields=['anuncio', 'usuario', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.anuncio_id} · {self.usuario_id} · {self.timestamp:%Y-%m-%d %H:%M:%S}"


class ClickAnuncio(models.Model):
    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name='clicks')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clicks_anuncio')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['anuncio', 'timestamp']),
            models.Index(fields=['anuncio', 'usuario', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.anuncio_id} · {self.usuario_id} · {self.timestamp:%Y-%m-%d %H:%M:%S}"