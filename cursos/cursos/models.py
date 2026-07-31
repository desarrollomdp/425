"""Modelos para la aplicación de cursos en Django.
Este módulo define los modelos para gestionar cursos, módulos, clases, asistencia, inscripciones y notas en un sistema educativo. 
También incluye modelos específicos para estudiantes e inscripciones del sistema Pen.
Modelos:
- Cursos: Representa un curso con sus detalles, incluyendo nombre, descripción, fechas, instructor, módulos asociados, y más.
- Modulos: Representa un módulo dentro de un curso, con detalles como nombre, descripción, recursos, carga horaria, y estado de aprobación.
- Clase: Representa una clase específica dentro de un curso, con detalles como nombre, descripción y fecha.
- Asistencia: Registra la asistencia de los estudiantes a las clases, asegurando que no haya duplicados.
- Inscripcion: Gestiona la inscripción de estudiantes a los cursos, incluyendo datos personales y documentación adjunta.
- Nota: Registra las notas de los estudiantes en los módulos, asegurando que un estudiante solo tenga una nota por módulo.
- EstudiantePen: Representa a los estudiantes del sistema Pen, con detalles como nombre, email y DNI.
- InscripcionPen: Gestiona las inscripciones de los estudiantes del sistema Pen a los cursos, incluyendo estado y documentación adjunta.
Relaciones:
- Cursos tiene una relación muchos a muchos con User (alumnos_inscriptos) y EstudiantePen"""
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models import Q
from multiselectfield import MultiSelectField

class Cursos(models.Model):
    nombre = models.CharField(max_length=255, help_text="El nombre no puede tener más de 25 caracteres.")
    descripcion = models.TextField(help_text="Campo de texto largo.")
    fecha_inicio = models.DateField(help_text="Fecha de inicio del curso.")
    fecha_fin = models.DateField(help_text="Fecha de finalización del curso.")
    max_estudiantes = models.PositiveIntegerField(help_text="Número máximo de estudiantes permitidos en el curso.")
    grupo_familia = models.CharField(max_length=100, help_text="Grupo o familia al que pertenece el curso.")
    aprobado = models.BooleanField(default=False)
    alumnos_inscriptos = models.ManyToManyField(
        User, 
        related_name="cursos_inscriptos", 
        blank=True, 
        help_text="Relación muchos a muchos con alumnos inscritos."
    )
     # 🔹 Nuevo campo para estudiantes del sistema Pen
    alumnos_inscriptos_pen = models.ManyToManyField(
        'EstudiantePen',
        related_name="cursos_inscriptos_pen",
        blank=True,
        help_text="Relación muchos a muchos con alumnos inscritos en el sistema Pen."
    )

    instructor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="cursos_creados", 
        help_text="Instructor del curso. Solo usuarios con rol de instructor pueden ser asignados."
    )
    modulos = models.ManyToManyField(
        'Modulos', 
        related_name="cursos_asociados", 
        blank=True, 
        help_text="Módulos que integran el curso."
    )
    
    # Opciones de lugar
    LUGAR_OPCIONES = [
        ('SEDE', 'Sede'),
        ('SUB_SEDE', 'Sub sede'),
        ('ANEXO', 'Anexo'),
    ]
    lugar = models.CharField(
        max_length=20,
        choices=LUGAR_OPCIONES,
        default='SEDE',
        help_text="Ubicación física donde se dicta el curso"
    )

    inscripcion_abierta = models.BooleanField(
        default=True,
        help_text="Indica si las inscripciones están abiertas para este curso."
    )

    cursando = models.BooleanField(
        default=True,
        help_text="Indica si el curso ya comenzó"
    )

    # Campos nuevos para días y horarios
    DIAS_OPCIONES = [
        ('LUNES', 'Lunes'),
        ('MARTES', 'Martes'),
        ('MIÉRCOLES', 'Miércoles'),
        ('JUEVES', 'Jueves'),
        ('VIERNES', 'Viernes'),
        ('SÁBADO', 'Sábado'),
        ('DOMINGO', 'Domingo'),
    ]
    dias = MultiSelectField(choices=DIAS_OPCIONES, blank=True, help_text="Días en que se dicta el curso")
    
    
    
    horario_inicio = models.TimeField(
        null=True, blank=True, 
        help_text="Horario de inicio del curso"
    )

    horario_fin = models.TimeField(
        null=True, blank=True, 
        help_text="Horario de finalización del curso"
    )
    # Agregar el campo dias como un campo específico de Cursos
    
    
    def dias_cursada(self):
        """Devuelve los días de cursada como lista de nombres legibles"""
        dias_dict = dict(self.DIAS_OPCIONES)
        return [dias_dict[dia] for dia in self.dias]
    
    def horario_formateado(self):
        if self.horario_inicio and self.horario_fin:
            return f"{self.horario_inicio.strftime('%H:%M')} - {self.horario_fin.strftime('%H:%M')}"
        return "Horario no definido"
    def vacantes_disponibles(self):
        """Calcula y devuelve el número de vacantes disponibles en el curso."""
        return self.max_estudiantes - self.alumnos_inscriptos.count()

    def save(self, *args, **kwargs):
        """Verifica que todos los módulos estén aprobados antes de marcar el curso como aprobado."""
        if self.pk:  # Solo verificar si el curso ya existe
            all_modulos_aprobados = not self.modulos.filter(~Q(estado_aprobado=True)).exists()
            self.aprobado = all_modulos_aprobados
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    def alumnos_inscriptos_nombres(self):
        """Devuelve una lista de nombres completos de los alumnos inscriptos."""
        return [f"{user.first_name} {user.last_name}" for user in self.alumnos_inscriptos.all()]

class Modulos(models.Model):
    nombre = models.CharField(max_length=255, help_text="Nombre del módulo.")
    descripcion = models.TextField(help_text="Descripción detallada del módulo.")
    recursos = models.FileField(
        upload_to='modulos/recursos/', 
        blank=True, 
        help_text="Solo archivos PDF.",
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    carga_horaria = models.IntegerField(help_text="Ingrese la carga horaria del módulo.")
    fecha_inicio_modulo = models.DateField(default=timezone.now)
    fecha_fin_modulo = models.DateField(default=timezone.now)
    DIAS_OPCIONES = [
        ('', 'Sin día asignado'),  # Opción por defecto
        ('LUNES', 'Lunes'),
        ('MARTES', 'Martes'),
        ('MIÉRCOLES', 'Miércoles'),
        ('JUEVES', 'Jueves'),
        ('VIERNES', 'Viernes'),
        ('SÁBADO', 'Sábado'),
        ('DOMINGO', 'Domingo'),
    ]
    
    dias = models.CharField(
        max_length=20,
        choices=DIAS_OPCIONES,
        default='',
        blank=True,
        help_text="Día en que se dicta el módulo"
    )
    instructor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="modulos_creados", 
        help_text="Instructor responsable del módulo."
    )
    
    nota = models.FloatField(
        help_text="Nota obtenida por los estudiantes en el módulo. Debe estar entre 0 y 100.",
        default=0.0
    )
    
    estado_aprobado = models.BooleanField(
        default=False, 
        help_text="Indica si el módulo está aprobado o no."
    )


    @property
    def horario_inicio(self):
        return self.curso_principal.horario_inicio if self.curso_principal else None

    @property
    def horario_fin(self):
        return self.curso_principal.horario_fin if self.curso_principal else None

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Guardar primero
        try:
            if self.pk:
                cursos = self.cursos_asociados.all()
                if cursos.exists() and not self.dias:
                    self.dias = cursos.first().dias
                    super().save(*args, **kwargs)  # Guardar nuevamente
        except Exception as e:
            print(f"Error al guardar días: {e}")  # Log para depuración

    def actualizar_estado_aprobacion(self):
        """Actualiza estado sin recursión"""
        nuevo_estado = self.nota >= 70
        if self.estado_aprobado != nuevo_estado:
            self.estado_aprobado = nuevo_estado
            self.save(update_fields=['estado_aprobado'])

    def __str__(self):
        return self.nombre

# Modelo para las clases dentro de un curso
class Clase(models.Model):
    # Relación con el curso al que pertenece la clase
    curso = models.ForeignKey(Cursos, related_name='clases', on_delete=models.CASCADE)
    
    # Nombre de la clase
    nombre = models.CharField(max_length=200)
    
    # Descripción de la clase
    descripcion = models.TextField()
    
    # Fecha en la que se dicta la clase
    fecha = models.DateField(default=timezone.now)

    def __str__(self):
        """Representación en texto de la clase."""
        return self.nombre

# Modelo para registrar la asistencia de los estudiantes
class Asistencia(models.Model):
    # Relación con la clase
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='asistencias')
    
    # Relación con el estudiante
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asistencias')
    
    # Estado de asistencia (presente o ausente)
    estado = models.CharField(max_length=10, choices=[('presente', 'Presente'), ('ausente', 'Ausente')], default='ausente')
    
    # Fecha de la asistencia
    fecha = models.DateField(default=timezone.now)
    
    # Relación con el curso
    curso = models.ForeignKey(Cursos, on_delete=models.CASCADE, related_name="asistencias")

    class Meta:
        # Garantiza que no haya duplicados en la asistencia de un estudiante a una clase en una fecha específica
        unique_together = ('clase', 'estudiante', 'fecha')

    def __str__(self):
        """Representación en texto de la asistencia."""
        return f"{self.estudiante.first_name} {self.estudiante.last_name} - {self.estado} - {self.clase.nombre}"

    def clean(self):
            """
            Validar:
            - No se puede registrar asistencia duplicada para un estudiante en la misma clase y fecha,
            excepto cuando se trata del mismo registro.
            """
            if Asistencia.objects.filter(
                clase=self.clase,
                estudiante=self.estudiante,
                fecha=self.fecha
            ).exclude(id=self.id).exists():  # Excluye el registro actual
                raise ValidationError("Ya existe un registro de asistencia para este estudiante en esta clase y fecha.")

 
class Inscripcion(models.Model):
    # Datos personales del estudiante
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email=models.EmailField(verbose_name="Email", default=None, blank=True)
    telefono = models.CharField(max_length=15)
    direccion = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()
    dni_numero = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Número de DNI"
    )
    # Documentación adjunta
    dni_frente = models.FileField(upload_to='dni_frente/')
    dni_reverso = models.FileField(upload_to='dni_reverso/')
    constancia_cuil = models.FileField(upload_to='constancia_cuil/')
    analitico_primaria = models.FileField(upload_to='analitico_primaria/', null=True, blank=True)
    analitico_primaria_dorso = models.FileField(
        upload_to='analitico_primaria_dorso/', 
        null=True, 
        blank=True, 
        default=None, 
        help_text="Imagen del dorso del analítico de primaria."
    )

    partido = models.CharField(max_length=100, blank=True, null=True)
    localidad = models.CharField(max_length=100, blank=True, null=True)
 
    # Nivel de estudios alcanzado
    estudios_maximos = models.CharField(
        max_length=50, 
        choices=[('primaria', 'Primaria'), ('secundaria', 'Secundaria')]
    )



    # Relación con el usuario y el curso
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscripciones')
    curso = models.ForeignKey(Cursos, on_delete=models.CASCADE)

    def __str__(self):
        """Representación en texto de la inscripción."""
        return f"Inscripción de {self.nombre} {self.apellido} al curso {self.curso}"

    def clean(self):
        """
        Validar:
        - El curso debe tener vacantes disponibles.
        - El estudiante no puede inscribirse a un curso que ya ha aprobado.
        """
        if self.curso.vacantes_disponibles() <= 0:
            raise ValidationError("El curso no tiene vacantes disponibles.")

class Nota(models.Model):
    estudiante = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="notas",
        help_text="Estudiante que recibe la nota."
    )
    modulo = models.ForeignKey(
        Modulos, 
        on_delete=models.CASCADE, 
        related_name="notas",
        help_text="Módulo al que pertenece la nota."
    )
    nota = models.FloatField(
        default=0.0, 
        help_text="Nota del estudiante en el módulo (de 0 a 100)."
    )
    fecha_asignacion = models.DateTimeField(
        auto_now=True, 
        help_text="Fecha en la que se asignó la nota."
    )
    
    class Meta:
        unique_together = ('estudiante', 'modulo')  # Un estudiante solo puede tener una nota por módulo

    def save(self, *args, **kwargs):
        """
        Corregido: Manejo optimizado de actualizaciones
        """
        # Actualizar estado del módulo
        self.modulo.actualizar_estado_aprobacion()
        
        # Actualizar estado de los cursos relacionados
        for curso in self.modulo.cursos_asociados.all():
            curso.aprobado = not curso.modulos.filter(estado_aprobado=False).exists()
            curso.save(update_fields=['aprobado'])

        super().save(*args, **kwargs)



class EstudiantePen(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Estudiante")
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI", default="0000")
    
    # Agrega aquí otros campos específicos que requiera el sistema pen
    # por ejemplo: curso_asignado, estado, etc.

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estudiante Pen"
        verbose_name_plural = "Estudiantes Pen"
        ordering = ['nombre']


class InscripcionPen(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('Rechazado', 'Rechazado'),
    ]
    estudiante = models.ForeignKey('EstudiantePen', on_delete=models.CASCADE, related_name='inscripciones')
    curso = models.ForeignKey('Cursos', on_delete=models.CASCADE, related_name='inscripciones')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    dni_frente_pen = models.ImageField(upload_to='dni_frente_pen/', blank=True)
    dni_reverso_pen = models.ImageField(upload_to='dni_reverso_pen/',blank=True)
    varios_pen = models.FileField(upload_to='varios_pen/',blank=True)
    analitico_primaria_pen = models.ImageField(upload_to='analitico_primaria_pen/', null=True, blank=True)
    maximo_alcanzado_choices = [
        ('PRIMARIA', 'Primaria'),
        ('SECUNDARIA', 'Secundaria'),
    ]
    
    maximo_alcanzado = models.CharField(
        max_length=20,
        choices=maximo_alcanzado_choices,
        default='PRIMARIA'  # Aquí estableces el valor por defecto
    )
    def __str__(self):
        return f"{self.estudiante.nombre} - {self.curso.nombre} ({self.estado})"

    class Meta:
        verbose_name = "Inscripción Pen"
        verbose_name_plural = "Inscripciones Pen"
        ordering = ['-fecha_inscripcion']