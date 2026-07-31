import threading
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from .models import Inscripcion, InscripcionPen, Clase

# ==========================================================
# 1. Hilo maestro para enviar CUALQUIER email en segundo plano
# (Le agregué soporte para HTML así te sirve para las clases)
# ==========================================================
class EmailThread(threading.Thread):
    def __init__(self, subject, message, from_email, recipient_list, html_message=None):
        self.subject = subject
        self.message = message
        self.recipient_list = recipient_list
        self.from_email = from_email
        self.html_message = html_message
        threading.Thread.__init__(self)

    def run(self):
        send_mail(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list,
            html_message=self.html_message,
            fail_silently=True
        )

# ==========================================================
# 2. Señal de Inscripción (Ahora en segundo plano)
# ==========================================================
@receiver(post_save, sender=Inscripcion)
def enviar_email_inscripcion(sender, instance, created, **kwargs):
    if created:
        # 1. Obtener mensaje dinámico del instructor o usar el fallback
        mensaje_cuerpo = instance.curso.mensaje_inscripcion
        
        if not mensaje_cuerpo or mensaje_cuerpo.strip() == "":
            mensaje_cuerpo = (
                f"¡Hola! Tu pre-inscripción al curso '{instance.curso.nombre}' se ha completado con éxito.\n\n"
                "Por favor, ponte en contacto con tu instructor a través de la sala de chat de nuestra plataforma "
                "para recibir más detalles sobre el inicio de clases, los días de cursada y los requisitos necesarios."
            )
        
        # 2. Armar la estructura del email
        subject = f"¡Tu pre-inscripción al curso {instance.curso.nombre} ha sido registrada!"
        message = (
            f"{mensaje_cuerpo}\n\n"
            "--------------------------------------------------\n"
            "RESUMEN DE TUS DATOS REGISTRADOS:\n"
            f"Alumno: {instance.nombre} {instance.apellido}\n"
            f"DNI: {instance.dni_numero}\n"
            f"Curso: {instance.curso.nombre}\n"
            "--------------------------------------------------\n\n"
            "Saludos cordiales,\n"
            "El equipo del CFP 425 NUESTRA SEÑORA DE LUJÁN"
        )
        
        from_email = 'cfp425informatica@gmail.com'
        recipient_list = [instance.email]
        
        # ACA DISPARAMOS EL HILO
        EmailThread(subject, message, from_email, recipient_list).start()

# ==========================================================
# 3. Señal de Estudiante PEN
# ==========================================================
@receiver(post_save, sender=InscripcionPen)
def add_estudiante_aprobado(sender, instance, **kwargs):
    if instance.estado.lower() == 'aprobado':
        if instance.estudiante not in instance.curso.alumnos_inscriptos_pen.all():
            instance.curso.alumnos_inscriptos_pen.add(instance.estudiante)
            print(f"✅ Estudiante {instance.estudiante.nombre} agregado a {instance.curso.nombre}")

# ==========================================================
# 4. Señal de Nueva Clase (Ahora en segundo plano real)
# ==========================================================
@receiver(post_save, sender=Clase)
def enviar_email_nueva_clase(sender, instance, created, **kwargs):
    if created:
        clase = instance
        curso = clase.curso
        instructor = curso.instructor
        alumnos = curso.alumnos_inscriptos.all()
        enlace_perfil = f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://cfp425.com.ar'}/profile/"
        
        for alumno in alumnos:
            try:
                mensaje_html = render_to_string('emails/nueva_clase.html', {
                    'alumno': alumno,
                    'instructor': instructor,
                    'clase': clase,
                    'curso': curso,
                    'enlace_perfil': enlace_perfil
                })
                
                # ACA DISPARAMOS EL HILO CON HTML INCLUIDO
                EmailThread(
                    subject=f'Nueva clase creada en {curso.nombre}',
                    message=f'Hola {alumno.get_full_name()}, el instructor {instructor.get_full_name()} creó la clase {clase.nombre} - Fecha: {clase.fecha.strftime("%d/%m/%Y")}. Consulta tu asistencia en tu perfil.',
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@cfp425.site',
                    recipient_list=[alumno.email],
                    html_message=mensaje_html
                ).start()
                
            except Exception as e:
                print(f"❌ Error al procesar email a {alumno.email}: {str(e)}")
        
        print(f"📧 Proceso de emails disparado en segundo plano para clase '{clase.nombre}' ({alumnos.count()} alumnos)")