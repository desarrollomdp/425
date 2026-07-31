from django import forms
from .models import Cursos, InscripcionPen, Modulos, Inscripcion,Clase, Nota, EstudiantePen
from django.db.models import Q

 
from django import forms
from .models import Cursos, Modulos

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
            'grupo_familia', 'modulos', 'lugar', 'inscripcion_abierta', 'cursando', 'dias', 'horario_inicio', 'horario_fin'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del curso'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción'}),
            'fecha_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'max_estudiantes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Máx. estudiantes'}),
            'grupo_familia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Grupo o familia'}),
            'lugar': forms.Select(attrs={'class': 'form-select'}),
            'modulos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'inscripcion_abierta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cursando': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dias': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'horario_inicio': forms.TimeInput(attrs={'class': 'form-control'}),
            'horario_fin': forms.TimeInput(attrs={'class': 'form-control'})
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
        curso.dias = ','.join(self.cleaned_data['dias'])  # Guardamos los días como string
        if commit:
            curso.save()
            self.save_m2m()
        return curso


class ModulosForm(forms.ModelForm):
    class Meta:
        model = Modulos
        fields = ['nombre', 'descripcion', 'recursos', 'carga_horaria', 
                  'fecha_inicio_modulo', 'fecha_fin_modulo', 'nota', 'dias']
        widgets = {
            'fecha_inicio_modulo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin_modulo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'dias': forms.Select(attrs={'class': 'form-control'}),
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
    analitico_primaria = forms.ImageField(
        required=False,
        label="Analítico de Primaria (opcional)",
        help_text="Solo requerido si no posee estudios secundarios"
    )
    # Agregar los nuevos campos aquí
    partido = forms.CharField(max_length=100, required=False, label="Partido")
    localidad = forms.CharField(max_length=100, required=False, label="Localidad")
    class Meta:
        model = Inscripcion
        fields = [
            'nombre', 
            'apellido',
            'email',
            'telefono',
            'direccion',
            'fecha_nacimiento',
            'dni_numero',
            'dni_frente',
            'dni_reverso',
            'constancia_cuil',
            'analitico_primaria',
            'analitico_primaria_dorso',
            'estudios_maximos',
            'partido',  # Agregar el campo partido
            'localidad',  # Agregar el campo localidad
            'curso'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'curso': forms.HiddenInput(),
            'estudios_maximos': forms.Select(attrs={'class': 'form-select'}),
            'dni_frente': forms.FileInput(attrs={'class': 'form-file'}),
            'dni_reverso': forms.FileInput(attrs={'class': 'form-file'}),
            'constancia_cuil': forms.FileInput(attrs={'class': 'form-file'}),
        }
        labels = {
            'dni_numero': 'Número de DNI',
            'estudios_maximos': 'Nivel educativo máximo alcanzado'
        }

    def __init__(self, *args, **kwargs):
        # Extraer el parámetro user de los kwargs antes de llamar al super
        self.user = kwargs.pop('user', None)  # ¡Esta es la línea clave que falta!
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        )
        # Lógica para email y campos de archivo
        if self.user:
            self.fields['email'].initial = self.user.email
            self.fields['email'].widget.attrs['readonly'] = True

        # Hacer campos de archivo no obligatorios en edición
        if self.instance and self.instance.pk:  # Si es una instancia existente
            self.fields['dni_frente'].required = False
            self.fields['dni_reverso'].required = False
            self.fields['constancia_cuil'].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        # Validar solo si es nuevo registro o se cambian los archivos
        if not self.instance:  # Creación
            if not cleaned_data.get('dni_frente'):
                self.add_error('dni_frente', 'Debe subir el frente de su DNI')
            # ... resto de validaciones originales
        else:  # Edición
            # Validar analítico primaria solo si cambia el estudio
            estudios = cleaned_data.get('estudios_maximos')
            if estudios == 'primaria' and not self.instance.analitico_primaria and not cleaned_data.get('analitico_primaria'):
                self.add_error('analitico_primaria', 'Debe adjuntar analítico primario si no posee estudios secundarios')

        return cleaned_data






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
        


# forms.py
def __init__(self, *args, **kwargs):
    instructor = kwargs.pop('instructor', None)
    super().__init__(*args, **kwargs)
    
    if instructor:
        # Obtener módulos del instructor + módulos ya asignados al curso
        self.fields['modulos'].queryset = Modulos.objects.filter(
            Q(instructor=instructor) | Q(cursos=self.instance)
        ).distinct()
    else:
        self.fields['modulos'].queryset = Modulos.objects.none()

    # Establecer selección inicial de módulos
    if self.instance.pk:
        self.initial['modulos'] = self.instance.modulos.values_list('id', flat=True)

class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = [
            'nombre', 'apellido', 'email', 'telefono', 'direccion', 
            'fecha_nacimiento', 'dni_numero', 'dni_frente', 'dni_reverso', 
            'constancia_cuil', 'analitico_primaria', 'analitico_primaria_dorso', 
            'partido', 'localidad', 'estudios_maximos', 'curso'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }