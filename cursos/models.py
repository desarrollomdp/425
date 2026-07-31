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
from cuentas.utils import (
    comprimir_imagen, 
    verificar_nitidez, 
    extraer_dni_ocr, 
    generar_ruta_inscripcion
)



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

    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        null=True,
        verbose_name="Fecha de creación",
        help_text="Fecha y hora en que se creó el curso."
    )
    
    mensaje_inscripcion = models.TextField(
        null=True,
        blank=True,
        verbose_name="Mensaje para alumnos inscriptos",
        help_text="Este mensaje se enviará por email automáticamente al estudiante cuando se pre-inscriba."
    )
    
    
    def dias_cursada(self):
        """Devuelve los días de cursada como lista de nombres legibles"""
        dias_dict = dict(self.DIAS_OPCIONES)
        return [dias_dict[dia] for dia in set(self.dias)]
    
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
    @property
    def esta_activo(self):
        """
        Determina si el curso está actualmente activo usando:
        1. Campo booleano 'cursando' (control manual)
        2. Fecha de finalización (control automático)
        """
        from django.utils import timezone
        return self.cursando and self.fecha_fin >= timezone.now().date()
    
    
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
    
    # Estado de la asistencia (presente, ausente, justificado, media falta)
    ESTADOS_ASISTENCIA = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('media_falta', 'Media Falta'),
    ]

    estado = models.CharField(max_length=12, choices=ESTADOS_ASISTENCIA, default='ausente')

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

 
"""class Inscripcion(models.Model):
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
        return f"Inscripción de {self.nombre} {self.apellido} al curso {self.curso}"

    def clean(self):
       
        if self.curso.vacantes_disponibles() <= 0:
            raise ValidationError("El curso no tiene vacantes disponibles.")
"""
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



class Inscripcion(models.Model):
    # Relaciones base
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscripciones')
    curso = models.ForeignKey(Cursos, on_delete=models.CASCADE)

    # Datos Personales
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(default="", blank=True)
    telefono = models.CharField(max_length=15)
    direccion = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()
    dni_numero = models.CharField(max_length=20, verbose_name="DNI")

    # Documentación Obligatoria (Solo fotos)
    # Nota: Usamos ImageField para forzar que sean imágenes
    # Documentación Obligatoria (Agregamos null=True para no romper registros viejos)
    dni_frente = models.ImageField(upload_to=generar_ruta_inscripcion, null=True, blank=True)
    dni_dorso = models.ImageField(upload_to=generar_ruta_inscripcion, null=True, blank=True)
    constancia_cuil = models.ImageField(upload_to=generar_ruta_inscripcion, null=True, blank=True)

    # Analítico (Todos aceptan nulos para la migración)
    analitico_1 = models.ImageField(upload_to=generar_ruta_inscripcion, null=True, blank=True)
    analitico_2 = models.ImageField(upload_to=generar_ruta_inscripcion, null=True, blank=True)
    analitico_3 = models.ImageField(upload_to=generar_ruta_inscripcion, null=True, blank=True)
    analitico_4 = models.ImageField(upload_to=generar_ruta_inscripcion, null=True, blank=True)

    # Otros campos
    partido = models.CharField(max_length=100, blank=True, null=True)
    localidad = models.CharField(max_length=100, blank=True, null=True)
    estudios_maximos = models.CharField(max_length=50, choices=[('primaria', 'Primaria'), ('secundaria', 'Secundaria')])
    certificado = models.FileField(upload_to='certificados/', null=True, blank=True)
    pago_contribucion = models.BooleanField(default=False)
    entrega_certificado = models.BooleanField(default=False)
    inscripcion_fisica = models.BooleanField(default=False, help_text="Indica si el estudiante entregó la documentación física.")


    trabaja = models.BooleanField(verbose_name="¿Estás trabajando?", null=True, blank=True)
    horario_trabajo = models.CharField(max_length=255, verbose_name="Días y horarios de trabajo", null=True, blank=True)

    estudia_otro_lado = models.BooleanField(verbose_name="¿Estás estudiando en otro lugar?", null=True, blank=True)
    horario_estudio = models.CharField(max_length=255, verbose_name="Días y horarios de estudio", null=True, blank=True)

    def clean(self):
        """
        Validaciones lógicas de nitidez e identidad con soporte para datos heredados.
        """
        print(f"\n[DEBUG-MODEL] --- Iniciando clean() para {self.nombre} {self.apellido} ---")
        # 1. Validar que el usuario tenga DNI en su perfil
        perfil = self.usuario.profile
        dni_perfil = str(perfil.dni).strip() if perfil.dni else None
        print(f"[DEBUG-MODEL] DNI Perfil: {dni_perfil}")
        
        if not dni_perfil:
            # Error claro si no completó el perfil
            raise ValidationError({
                'dni_numero': "No tiene un DNI cargado en su perfil. Por favor, complete ese campo en su configuración de usuario antes de inscribirse."
            })

        # Intentamos obtener los datos actuales de la base de datos si es una edición
        instancia_previa = None
        if self.pk:
            try:
                # Usamos .objects.only para ser eficientes y solo traer lo necesario
                instancia_previa = Inscripcion.objects.get(pk=self.pk)
            except Inscripcion.DoesNotExist:
                pass

        # --- VALIDACIÓN DNI FRENTE (Nitidez + OCR) ---
        if self.dni_frente:
            # Solo validamos si es una inscripción nueva o si el archivo cambió
            es_archivo_nuevo = True
            if instancia_previa and instancia_previa.dni_frente == self.dni_frente:
                es_archivo_nuevo = False
            
            if es_archivo_nuevo:
                # A. Validar Nitidez
                # if not verificar_nitidez(self.dni_frente):
                #     raise ValidationError({
                #         'dni_frente': "La foto del DNI frontal no es legible (está borrosa). Por favor enfoca bien y vuelve a subirla."
                #     })
                
                # B. Validar Identidad vía OCR
                # dnis_detectados = extraer_dni_ocr(self.dni_frente)
                
                # if dnis_detectados is None:
                #     print(f"[DEBUG-MODEL] ⚠️ Saltando validación OCR por error técnico (Tesseract probablemente no instalado).")
                # elif dni_perfil not in dnis_detectados:
                #     print(f"[DEBUG-MODEL] ❌ DNI {dni_perfil} no encontrado en la lista: {dnis_detectados}")
                #     raise ValidationError({
                #         'dni_frente': f"El documento de la foto no coincide con el DNI de su perfil ({dni_perfil}). Verifique que la foto sea correcta y esté bien iluminada."
                #     })
                # else:
                #     print(f"[DEBUG-MODEL] ✅ DNI verificado exitosamente vía OCR.")
                
                # VALIDACIÓN SIMPLE (Reemplazo de AI)
                if str(self.dni_numero).strip() != dni_perfil:
                     raise ValidationError({
                        'dni_numero': f"El DNI ingresado ({self.dni_numero}) no coincide con el DNI de tu perfil ({dni_perfil})."
                    })

        # --- VALIDACIÓN DNI DORSO (Solo Nitidez) ---
        if self.dni_dorso:
            es_archivo_nuevo = True
            if instancia_previa and instancia_previa.dni_dorso == self.dni_dorso:
                es_archivo_nuevo = False
                
            if es_archivo_nuevo:
                pass
                # if not verificar_nitidez(self.dni_dorso):
                #     raise ValidationError({
                #         'dni_dorso': "La foto del DNI reverso no es legible. Por favor enfoca bien y vuelve a subirla."
                #     })

        # --- VALIDACIÓN CUIL (Solo Nitidez) ---
        if self.constancia_cuil:
            es_archivo_nuevo = True
            if instancia_previa and instancia_previa.constancia_cuil == self.constancia_cuil:
                es_archivo_nuevo = False
                
            if es_archivo_nuevo:
                pass
                # if not verificar_nitidez(self.constancia_cuil):
                #     raise ValidationError({
                #         'constancia_cuil': "La foto de la constancia de CUIL no es legible. Recuerda que debe ser una foto nítida de la constancia."
                #     })

        # --- VALIDACIÓN ANALÍTICO 1 (Solo Nitidez) ---
        # Solo validamos el primero ya que es el obligatorio
        if self.analitico_1:
            es_archivo_nuevo = True
            if instancia_previa and instancia_previa.analitico_1 == self.analitico_1:
                es_archivo_nuevo = False
                
            if es_archivo_nuevo:
                pass
                # if not verificar_nitidez(self.analitico_1):
                #     raise ValidationError({
                #         'analitico_1': "La foto del analítico no es suficientemente clara. Por favor intenta tomarla con mejor iluminación."
                #     })

        if self.trabaja and not self.horario_trabajo:
            raise ValidationError({
                'horario_trabajo': "Si indicaste que trabajas, debes completar tus días y horarios."
            })

        # Si pone que estudia, exigimos el horario.
        if self.estudia_otro_lado and not self.horario_estudio:
            raise ValidationError({
                'horario_estudio': "Si indicaste que estudias en otro lugar, debes completar tus días y horarios."
            })

    def save(self, *args, **kwargs):
        # Aplicamos la compresión WebP antes de enviar a R2
        if self.dni_frente:
            self.dni_frente = comprimir_imagen(self.dni_frente, f"dni_frente_{self.dni_numero}")
        if self.dni_dorso:
            self.dni_dorso = comprimir_imagen(self.dni_dorso, f"dni_dorso_{self.dni_numero}")
        if self.constancia_cuil:
            self.constancia_cuil = comprimir_imagen(self.constancia_cuil, f"cuil_{self.dni_numero}")
        
        # Comprimir analíticos si existen
        if self.analitico_1:
            self.analitico_1 = comprimir_imagen(self.analitico_1, f"analitico_1_{self.dni_numero}")
        if self.analitico_2:
            self.analitico_2 = comprimir_imagen(self.analitico_2, f"analitico_2_{self.dni_numero}")
        if self.analitico_3:
            self.analitico_3 = comprimir_imagen(self.analitico_3, f"analitico_3_{self.dni_numero}")
        if self.analitico_4:
            self.analitico_4 = comprimir_imagen(self.analitico_4, f"analitico_4_{self.dni_numero}")

        print(f"[DEBUG-MODEL] Intentando super().save()...")
        super(Inscripcion, self).save(*args, **kwargs)
        print(f"[DEBUG-MODEL] ✅ super().save() completado.")


class EstudiantesEliminados(models.Model):
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eliminaciones_como_estudiante')
    curso = models.ForeignKey(Cursos, on_delete=models.CASCADE, related_name='estudiantes_eliminados')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eliminaciones_como_instructor')
    motivo = models.TextField(help_text="Motivo por el cual el estudiante fue eliminado del curso.")
    fecha_eliminacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.estudiante.get_full_name()} eliminado de {self.curso.nombre} por {self.instructor.get_full_name()}"

    class Meta:
        verbose_name = "Estudiante Eliminado"
        verbose_name_plural = "Estudiantes Eliminados"
        ordering = ['-fecha_eliminacion']

