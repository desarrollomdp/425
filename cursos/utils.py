from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def enviar_email_confirmacion(inscripcion):
    """ Envía un email al estudiante confirmando la inscripción """
    
    asunto = "Confirmación de pre- Inscripción - CFP 425"
    mensaje_html = render_to_string("emails/confirmacion_inscripcion.html", {
        "nombre": inscripcion.nombre,
        "apellido": inscripcion.apellido,
        "curso": inscripcion.curso.nombre,
    })
    
    send_mail(
        asunto,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [inscripcion.usuario.email],  # Enviar al email del usuario
        html_message=mensaje_html,
    )
