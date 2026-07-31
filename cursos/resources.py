













































































































































































































































































from import_export import resources, fields, widgets
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from django.contrib.auth.models import User
from .models import Cursos
from .models import Modulos

class CursosResource(resources.ModelResource):
    instructor = fields.Field(
        column_name='instructor',
        attribute='instructor',
        widget=ForeignKeyWidget(User, 'username')  # <-- ¡Agrega una coma aquí!
    )
    
    modulos = fields.Field(
        column_name='modulos',
        attribute='modulos',
        widget=ManyToManyWidget(Modulos, field='id', separator=',')
    )
    
    dias = fields.Field(
        column_name='dias',
        attribute='dias',
        widget=widgets.JSONWidget(),
        default=[]
    )

    # Campos de tiempo corregidos (sin 'required')
    horario_inicio = fields.Field(
        column_name='horario_inicio',
        attribute='horario_inicio',
        widget=widgets.TimeWidget('%H:%M'),  # Formato 24h
        default=None  # Permite valores nulos
    )
    
    horario_fin = fields.Field(
        column_name='horario_fin',
        attribute='horario_fin',
        widget=widgets.TimeWidget('%H:%M'),
        default=None
    )

    class Meta:
        model = Cursos
        skip_unchanged = True
        import_id_fields = ()  # Ignora el campo 'id'
        fields = [
            'nombre',
            'descripcion',
            'fecha_inicio',
            'fecha_fin',
            'max_estudiantes',
            'grupo_familia',
            'aprobado',
            'lugar',
            'inscripcion_abierta',
            'cursando',
            'dias',
            'horario_inicio',
            'horario_fin',
            'instructor',
            'modulos'
        ]







class ModulosResource(resources.ModelResource):
    # Campos especiales (relaciones y lógica personalizada)
    instructor = fields.Field(
        column_name='instructor',
        attribute='instructor',
        widget=ForeignKeyWidget(User, 'username'))
    
    

    # Campos de fecha con formato latino
    fecha_inicio_modulo = fields.Field(
        widget=widgets.DateWidget('%d/%m/%Y')
    )
    
    fecha_fin_modulo = fields.Field(
        widget=widgets.DateWidget('%d/%m/%Y')
    )

    class Meta:
        model = Modulos
        skip_unchanged = True
        import_id_fields = []
        fields = [
            'nombre', 
            'descripcion', 
            'recursos',
            'carga_horaria', 
            'fecha_inicio_modulo', 
            'fecha_fin_modulo', 
            'instructor', 
            'nota'
        ]
        export_order = fields

    def before_import_row(self, row, **kwargs):
        """Calcula estado_aprobado basado en la nota (no necesita incluirse en el Excel)"""
        try:
            nota = float(row.get('nota', 0))
            row['estado_aprobado'] = '1' if nota >= 70 else '0'
        except ValueError:
            row['estado_aprobado'] = '0'