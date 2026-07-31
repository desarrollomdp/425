# mensajes/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Mensaje_socket

@receiver(post_save, sender=Mensaje_socket)
def enviar_email_nuevo_mensaje(sender, instance, created, **kwargs):
    """
    Signal para enviar email automáticamente cuando se crea un nuevo mensaje
    """
    if created:
        # Solo enviar si el mensaje tiene contenido o es un archivo adjunto
        destinatario = instance.receptor
        remitente = instance.emisor
        
        # Preparar extracto del contenido (máximo 100 caracteres)
        if instance.contenido:
            extracto = instance.contenido[:100]
            contenido_largo = len(instance.contenido) > 100
        else:
            extracto = "[Archivo adjunto]"
            contenido_largo = False
        
        # Generar enlace a la conversación
        # Intentar usar settings.SITE_URL, si no existe construir un fallback seguro
        site_base = getattr(settings, 'SITE_URL', '')
        if not site_base:
            hosts = getattr(settings, 'ALLOWED_HOSTS', []) or []
            host = hosts[0] if hosts else ''
            if host:
                if host.startswith('http'):
                    site_base = host.rstrip('/')
                else:
                    protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
                    site_base = f"{protocol}://{host}".rstrip('/')

        if site_base:
            enlace_conversacion = f"{site_base}/mensajes/conversacion/{remitente.id}/"
        else:
            # Fallback relativo (funciona en el mismo host)
            enlace_conversacion = f"/mensajes/conversacion/{remitente.id}/"
        
        try:
            # Renderizar template HTML
            mensaje_html = render_to_string('emails/nuevo_mensaje.html', {
                'destinatario': destinatario,
                'remitente': remitente,
                'extracto': extracto,
                'contenido_largo': contenido_largo,
                'enlace_conversacion': enlace_conversacion
            })
            
            # Enviar email
            send_mail(
                subject=f'Nuevo mensaje de {remitente.get_full_name()}',
                message=f'Hola {destinatario.get_full_name()}, has recibido un nuevo mensaje de {remitente.get_full_name()}. Contenido: {extracto}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario.email],
                html_message=mensaje_html,
                fail_silently=True,  # No interrumpir si falla el envío
            )
            print(f"✅ Email enviado a {destinatario.email} por nuevo mensaje")
            
        except Exception as e:
            print(f"❌ Error al enviar email de nuevo mensaje: {str(e)}")
