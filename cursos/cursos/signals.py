from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Inscripcion, InscripcionPen
from django.contrib.auth.models import User

@receiver(post_save, sender=Inscripcion)
def enviar_email_inscripcion(sender, instance, created, **kwargs):
    if created:
        subject = "Confirmación de Inscripción al Curso"
        
        # Formateo de fechas (si existen)
        fecha_nacimiento = instance.fecha_nacimiento.strftime("%d/%m/%Y") if instance.fecha_nacimiento else "No especificado"
        curso_inicio = instance.curso.fecha_inicio.strftime("%d/%m/%Y") if instance.curso.fecha_inicio else "No especificado"
        curso_fin = instance.curso.fecha_fin.strftime("%d/%m/%Y") if instance.curso.fecha_fin else "No especificado"
        # Obtención de los días del curso
        dias_curso = ", ".join(instance.curso.dias_cursada()) if instance.curso.dias else "No especificados"
        
        # Mensaje base con la información del usuario y del curso
        message = (
            f"Hola {instance.nombre} {instance.apellido},\n\n"
            f"Te confirmamos que tu pre-inscripción al curso '{instance.curso.nombre}' ha sido exitosa.\n\n"
            "A continuación, se detalla la información registrada en tu inscripción:\n"
            "--------------------------------------------------\n"
            "DATOS PERSONALES:\n"
            f"Nombre: {instance.nombre}\n"
            f"Apellido: {instance.apellido}\n"
            f"Email: {instance.email}\n"
            f"Teléfono: {instance.telefono}\n"
            f"Dirección: {instance.direccion}\n"
            f"Fecha de Nacimiento: {fecha_nacimiento}\n"
            f"Número de DNI: {instance.dni_numero}\n"
            f"Nivel Educativo: {instance.estudios_maximos}\n"
            f"Partido: {instance.partido}\n"
            f"Localidad: {instance.localidad}\n\n"
            "DATOS DEL CURSO:\n"
            f"Curso: {instance.curso.nombre}\n"
            f"Fecha de Inicio: {curso_inicio}\n"
            f"Fecha de Fin: {curso_fin}\n"
            f"Horario: {instance.curso.horario_formateado()}\n"
            f"Días de Clases: {dias_curso}\n"
            "--------------------------------------------------\n\n"
        )
        
        # Instrucciones para la reunión según el lugar de inscripción
        if instance.curso.lugar == "SEDE":
            message += (
                "IMPORTANTE:\n"
                "- El instructor se pondra en contacto para brindarle la información del inicio de clases! SALUDOS!\n\n"
            )
        elif instance.curso.lugar == "ANEXO":
            message += (
                "IMPORTANTE:\n"
                "- Deberás presentarte a una reunión informativa en el Anexo - Rafael Castillo el 6 de marzo, "
                "en el horario de tu curso.\n\n"
            )
        else:
            message += (
                "IMPORTANTE:\n"
                "-El instructor se pondra en contacto para brindarle la información del inicio de clases! SALUDOS!\n\n"
            )
        
        # Documentos requeridos y link de descarga de la planilla
        message += (
            "Recuerda que deberás presentar los siguientes documentos:\n"
            "- 2 fotocopias de tu DNI\n"
            "- 2 fotocopias de tu constancia de CUIL (Si el DNI tiene cuil no traer CUIl)\n"
            "- La planilla de inscripción impresa y completada (Descarga la planilla aquí: https://cfp425.site/media/documentos/planilla_de_inscripci%C3%B3n_mas_encuesta1.pdf)\n\n"
            "Si tienes alguna consulta, no dudes en contactarnos.\n\n"
            "Saludos cordiales,\n"
            "El equipo del Centro de Formación Profesional 425 NUESTRA SEÑORA DE LUJÁN"
        )
        
        from_email = 'leandroezequielfernandez136@gmail.com'
        recipient_list = [instance.email]
        send_mail(subject, message, from_email, recipient_list)


@receiver(post_save, sender=InscripcionPen)
def add_estudiante_aprobado(sender, instance, **kwargs):
    """Si el estudiante es aprobado, lo agrega a la lista de inscriptos en el curso."""
    if instance.estado.lower() == 'aprobado':
        if instance.estudiante not in instance.curso.alumnos_inscriptos_pen.all():
            instance.curso.alumnos_inscriptos_pen.add(instance.estudiante)
            print(f"✅ Estudiante {instance.estudiante.nombre} agregado a {instance.curso.nombre}")