from django import forms
from .models import Cursos, InscripcionPen, Modulos, Inscripcion,Clase, Nota, EstudiantePen
from django.db.models import Q
from django import forms
from .models import Cursos, Modulos
from .choices import PARTIDOS_PRINCIPALES, LOCALIDADES_POR_PARTIDO

class CursosForm(forms.ModelForm):
    DIAS_CHOICES = [
        ('LUNES', 'Lunes'),
        ('MARTES', 'Martes'),
        ('MIÉRCOLES', 'Miércoles'),
        ('JUEVES', 'Jueves'),
        ('VIERNES', 'Viernes'),
        ('SÁBADO', 'Sábado'),
        ('DOMINGO', 'Domingo'),
    ]

    
    dias = forms.MultipleChoiceField(
        choices=DIAS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

    horario_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-check-input',
            'type': 'time'
        }),
        required=False
    )
    
    horario_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-check-input',
            'type': 'time'
        }),
        required=False
    )

    class Meta:
        model = Cursos
        fields = [
            'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'max_estudiantes',
            'grupo_familia', 'modulos', 'lugar', 'inscripcion_abierta', 'cursando', 'dias', 'horario_inicio', 'horario_fin', 'mensaje_inscripcion'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del curso'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción'}),
            'fecha_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'max_estudiantes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Máx. estudiantes'}),
            'grupo_familia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Grupo o familia'}),
            'lugar': forms.Select(attrs={'class': 'form-select'}),
            'inscripcion_abierta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cursando': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dias': forms.CheckboxSelectMultiple(attrs={'class': 'hidden peer'}),
            'modulos': forms.CheckboxSelectMultiple(attrs={'class': 'hidden peer'}),
            'horario_inicio': forms.TimeInput(attrs={'class': 'form-control'}),
            'horario_fin': forms.TimeInput(attrs={'class': 'form-control'}),
            'mensaje_inscripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe aquí la información del curso que quieres enviar por email a los alumnos pre-inscriptos automáticamente.'})
        }

    def __init__(self, *args, **kwargs):
        instructor = kwargs.pop('instructor', None)
        super().__init__(*args, **kwargs)

        if instructor:
            self.fields['modulos'].queryset = Modulos.objects.filter(instructor=instructor)
        else:
            self.fields['modulos'].queryset = Modulos.objects.none()

        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio:
                self.initial['fecha_inicio'] = self.instance.fecha_inicio.strftime('%Y-%m-%d')
            if self.instance.fecha_fin:
                self.initial['fecha_fin'] = self.instance.fecha_fin.strftime('%Y-%m-%d')

            # Convertimos los días en una lista para que se marquen en el formulario
            if self.instance.dias:
                 self.initial['dias'] = self.instance.dias
            
            # Convertir los horarios de inicio y fin
            if self.instance.horario_inicio:
                self.initial['horario_inicio'] = self.instance.horario_inicio.strftime('%H:%M')
            if self.instance.horario_fin:
                self.initial['horario_fin'] = self.instance.horario_fin.strftime('%H:%M')

    def save(self, commit=True):
        curso = super().save(commit=False)
        # curso.dias ya es manejado por MultiSelectField/ModelForm
        if commit:
            curso.save()
            self.save_m2m()
        return curso


class ModulosForm(forms.ModelForm):
    class Meta:
        model = Modulos
        fields = ['nombre', 'descripcion', 'recursos', 'carga_horaria', 
                  'fecha_inicio_modulo', 'fecha_fin_modulo']
        widgets = {
            'fecha_inicio_modulo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin_modulo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            
        }

    def __init__(self, *args, **kwargs):
        super(ModulosForm, self).__init__(*args, **kwargs)
        # Si la instancia existe, formateamos los campos de fecha para que se muestren correctamente
        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio_modulo:
                self.initial['fecha_inicio_modulo'] = self.instance.fecha_inicio_modulo.strftime('%Y-%m-%d')
            if self.instance.fecha_fin_modulo:
                self.initial['fecha_fin_modulo'] = self.instance.fecha_fin_modulo.strftime('%Y-%m-%d')


class AsistenciaEstudianteForm(forms.Form):
    """
    Formulario para gestionar la asistencia de múltiples estudiantes
    con fecha fija correspondiente a la clase
    """
    
    # Campo para seleccionar todos los estudiantes
    seleccionar_todos = forms.BooleanField(
        required=False,
        label='Marcar Todos como Presentes',
        widget=forms.CheckboxInput(attrs={
            'class': 'select-all-checkbox',
            'data-action': 'select-all'
        })
    )

    def __init__(self, *args, **kwargs):
        curso = kwargs.pop('curso', None)
        clase = kwargs.pop('clase', None)
        super().__init__(*args, **kwargs)

        # La fecha será un campo oculto con el valor de la clase
        if clase:
            self.fields['fecha'] = forms.DateField(
                initial=clase.fecha,
                widget=forms.HiddenInput(),  # Campo oculto
                disabled=True  # No se puede modificar
            )

        if curso:
            # Ordenar estudiantes por apellido y nombre
            estudiantes = curso.alumnos_inscriptos.all().order_by('last_name', 'first_name')
            
            for estudiante in estudiantes:
                field_name = f'estado_{estudiante.id}'
                self.fields[field_name] = forms.ChoiceField(
                choices=[
                    ('presente', 'Presente'),
                    ('ausente', 'Ausente'),
                    ('media_falta', 'Media Falta'),
                ],
                initial='ausente',
                label=f"{estudiante.last_name}, {estudiante.first_name}",
                widget=forms.RadioSelect(
                    attrs={
                        'class': 'attendance-radio',
                        'data-student-id': estudiante.id
                    }
                )
            )


    def get_estudiantes_count(self):
        """Retorna el número total de estudiantes en el formulario"""
        return len([f for f in self.fields if f.startswith('estado_')])




class RegistroCursoForm(forms.ModelForm):
    # Definimos los campos de fecha y archivos con widgets específicos
    fecha_nacimiento = forms.DateField(
        label="Fecha de Nacimiento",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    partido = forms.ChoiceField(
        choices=PARTIDOS_PRINCIPALES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Partido *"
    )
    localidad = forms.ChoiceField(
        choices=[('', 'Seleccione partido primero')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Localidad *"
    )
    # Campos de Documentación con ayuda visual
    dni_frente = forms.ImageField(required=True,
        label="DNI Frente (Foto nítida)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    dni_dorso = forms.ImageField(required=True,
        label="DNI Dorso (Foto nítida)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    constancia_cuil = forms.ImageField(required=True,
        label="Constancia de CUIL (Foto)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    
    # Slots de Analítico
    analitico_1 = forms.ImageField(required=True,
        label="Analítico - Página 1 (Obligatorio)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    analitico_2 = forms.ImageField(
        label="Analítico - Página 2 (Opcional)",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    analitico_3 = forms.ImageField(
        label="Analítico - Página 3 (Opcional)",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    analitico_4 = forms.ImageField(
        label="Analítico - Página 4 (Opcional)",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    email = forms.EmailField(
        label="Email de la Cuenta",
        required=False, # No lo requerimos del POST porque lo tomaremos del User
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-light', # Gris claro para indicar que está bloqueado
            'readonly': 'readonly',
            'disabled': 'disabled',  # Esto previene que se envíe en el POST
        })
    )
    class Meta:
        model = Inscripcion
        # Incluimos todos los campos en el orden lógico para el usuario
        fields = [
            'nombre', 'apellido', 'email', 'telefono', 'direccion', 
            'fecha_nacimiento', 'dni_numero', 'dni_frente', 'dni_dorso', 
            'constancia_cuil', 'analitico_1', 'analitico_2', 'analitico_3', 
            'analitico_4', 'partido', 'localidad', 'estudios_maximos', 'trabaja', 'horario_trabajo', 'estudia_otro_lado', 'horario_estudio'
        ]
        
        # Aplicamos estilos de Bootstrap a los campos de texto y selects
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1122334455'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle y número'}),
            'dni_numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Solo números'}),
            'partido': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),
            'estudios_maximos': forms.Select(attrs={'class': 'form-select'}),
            'trabaja': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'horario_trabajo': forms.TextInput(attrs={'class': 'form-control'}),
            'estudia_otro_lado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'horario_estudio': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control bg-light',
                'readonly': 'readonly',
                'disabled': 'disabled',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extraer el usuario si se pasa como argumento
        self.user = kwargs.pop('user', None)
        print(f"\n[DEBUG-FORM] --- Inicializando RegistroCursoForm ---")
        print(f"[DEBUG-FORM] Usuario recibido: {self.user.username if self.user else 'None'}")
        super(RegistroCursoForm, self).__init__(*args, **kwargs)
        
        # Establecer el valor inicial del email con el email del usuario
        if self.user:
            self.fields['email'].initial = self.user.email
            # Asignar usuario a la instancia para validaciones del modelo (clean)
            if not self.instance.pk:
                self.instance.usuario = self.user
                print(f"[DEBUG-FORM] Usuario asignado a la instancia.")
        
        # Hacer que el campo email no sea requerido para la validación
        self.fields['email'].required = False
        
        # Lógica para cargar localidades dinámicamente
        partido_seleccionado = None
        
        # 1. Prioridad: Datos del POST (si el usuario ya seleccionó algo y hubo error)
        if 'partido' in self.data:
            try:
                partido_seleccionado = self.data.get('partido')
            except (ValueError, TypeError):
                pass
        # 2. Secundaria: Datos de la instancia (si está editando)
        elif self.instance and self.instance.pk and self.instance.partido:
            partido_seleccionado = self.instance.partido

        # Cargar opciones si hay partido, sino dejar vacío
        if partido_seleccionado:
            localidades = LOCALIDADES_POR_PARTIDO.get(partido_seleccionado, [])
            if localidades:
                self.fields['localidad'].choices = localidades
            else:
                self.fields['localidad'].choices = [('', 'No hay localidades disponibles')]
        else:
             self.fields['localidad'].choices = [('', 'Seleccione partido primero')]




class ClaseForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = ['nombre', 'descripcion', 'fecha', 'curso']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'curso': forms.HiddenInput(),  # Campo oculto
        }

class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['nota']
        widgets = {
            'nota': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 0.1}),
        }


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = EstudiantePen
        fields = ['nombre','dni']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del estudiante'
            }),
        }



class InscripcionPenForm(forms.ModelForm):
    class Meta:
        model = InscripcionPen
        fields = ['curso', 'dni_frente_pen','dni_reverso_pen','varios_pen','analitico_primaria_pen','maximo_alcanzado']
        maximo_alcanzado = forms.ChoiceField(
            choices=InscripcionPen.maximo_alcanzado_choices,
            initial='PRIMARIA'  # Valor por defecto
        )
        widgets = {
            'curso': forms.Select(attrs={'class': 'form-control'}),
            
        }
        




