from django.contrib import admin
from .models import Cursos, InscripcionPen, Modulos, Inscripcion,Asistencia,Clase, Nota, EstudiantePen
from django.contrib import admin
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings
import base64
from .resources import CursosResource, ModulosResource
from import_export.admin import ImportExportModelAdmin
from io import BytesIO
import zipfile
import csv

class EstudiantepenAdmin(admin.ModelAdmin):
    list_display=('nombre','dni')

@admin.register(InscripcionPen)
class InscripcionPenAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'curso', 'estado', 'fecha_inscripcion')
    list_filter = ('estado', 'fecha_inscripcion')
    search_fields = ('estudiante__nombre', 'curso__nombre')


class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ( 'estudiante', 'fecha', 'estado','curso','clase')  # Campos que se mostrarán en la lista
    list_filter = ( 'estado', 'fecha','curso','clase')  # Filtros para facilitar la búsqueda
    search_fields = ('estudiante__username', 'curso__nombre')  # Permite buscar por nombre de estudiante y curso
    list_per_page = 20  # Limita el número de registros por página en la lista

    # Si quieres permitir la edición de las asistencias directamente desde el admin
    # también puedes usar el siguiente código:
    fields = ('curso', 'estudiante', 'estado','clase')  # Especifica el orden de los campos


 

class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'usuario', 'curso', 'fecha_nacimiento', 'localidad', 'partido')
    search_fields = ('apellido', 'nombre', 'usuario__username', 'curso__nombre')
    date_hierarchy = 'fecha_nacimiento'
    list_filter=('curso','localidad')
    actions = ['exportar_pdf']

    def generar_pdf(self, inscripcion):
        """Genera un PDF para una inscripción específica con todos los documentos."""
        template_path = 'admin/pdf_template.html'
        template = get_template(template_path)

        # Diccionario para almacenar todas las imágenes en base64
        documentos = {
            'dni_frente': None,
            'dni_reverso': None,
            'constancia_cuil': None,
            'analitico_primaria': None
        }

        # Procesar cada documento
        for doc_field in documentos.keys():
            doc_file = getattr(inscripcion, doc_field)
            if doc_file:
                doc_path = os.path.join(settings.MEDIA_ROOT, str(doc_file))
                try:
                    with open(doc_path, "rb") as f:
                        documentos[doc_field] = base64.b64encode(f.read()).decode('utf-8')
                except Exception as e:
                    print(f"[ERROR] Error procesando {doc_field}: {e}")

        context = {
            'inscripcion': inscripcion,
            'documentos': documentos,  # Pasamos todos los documentos
        }

        html = template.render(context)
        pdf_bytes = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf_bytes)

        if pisa_status.err:
            return None

        return pdf_bytes.getvalue()

    def exportar_pdf(self, request, queryset):
        """Exporta PDFs individuales o genera un ZIP si hay más de uno seleccionado."""
        if queryset.count() == 1:
            # Si hay solo un elemento seleccionado, descarga el PDF directamente
            inscripcion = queryset.first()
            pdf_content = self.generar_pdf(inscripcion)
            if not pdf_content:
                return HttpResponse("Error al generar el PDF", status=500)

            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="inscripcion_{inscripcion.id}_{inscripcion.nombre}.pdf"'
            return response

        # Si hay múltiples elementos, crea un ZIP con todos los PDFs
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for inscripcion in queryset:
                pdf_content = self.generar_pdf(inscripcion)
                if pdf_content:
                    filename = f'inscripcion_{inscripcion.id}_{inscripcion.nombre}.pdf'
                    zip_file.writestr(filename, pdf_content)

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="inscripciones.zip"'
        return response

    exportar_pdf.short_description = "Exportar seleccionados como PDF o ZIP"

admin.site.register(Inscripcion, InscripcionAdmin)





# Inline para gestionar los estudiantes inscritos en un curso
class AlumnosInscritosInline(admin.TabularInline):
    model = Cursos.alumnos_inscriptos.through  # Usamos el modelo intermedio de la relación ManyToMany
    extra = 0  # No mostrar formularios adicionales vacíos
    verbose_name = "Estudiante Inscrito"
    verbose_name_plural = "Estudiantes Inscritos"

    # Campos que se mostrarán en la lista
    list_display = ('username', 'email', 'fecha_inscripcion')

    def fecha_inscripcion(self, obj):
        """
        Método para mostrar la fecha de inscripción del estudiante.
        """
        # Aquí puedes personalizar cómo obtener la fecha de inscripción si la tienes en otro modelo.
        return "Fecha no disponible"  # Cambia esto según tu lógica

    fecha_inscripcion.short_description = "Fecha de Inscripción"

class InscripcionPenInline(admin.TabularInline):
    model = InscripcionPen
    extra = 0  # No mostrar formularios adicionales vacíos
    verbose_name = "Alumno Preinscrito"
    verbose_name_plural = "Alumnos Preinscritos"
    fields = ('estudiante', 'estado', 'fecha_inscripcion')
    readonly_fields = ('estudiante', 'estado', 'fecha_inscripcion')

@admin.register(Cursos)
class CursosAdmin(ImportExportModelAdmin):  # <-- Manteniendo la herencia de import/export
    resource_class = CursosResource
    
    fields = (
        'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 
        'max_estudiantes', 'grupo_familia', 'instructor', 'modulos',
        'lugar', 'inscripcion_abierta', 'cursando', 'dias',
        'horario_inicio', 'horario_fin'
    )

    list_display = (
        'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 
        'max_estudiantes', 'vacantes_disponibles', 'lugar',
        'inscripcion_abierta'
    )

    inlines = [AlumnosInscritosInline, InscripcionPenInline]  # <-- Agregamos el nuevo inline

    actions = ['exportar_estudiantes_excel']

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return [field for field in fields if field != 'alumnos_inscriptos']

    def exportar_estudiantes_excel(self, request, queryset):
        """Exporta los estudiantes inscritos en un curso a un archivo Excel."""
        if queryset.count() != 1:
            self.message_user(request, "Por favor, seleccione un solo curso para exportar.", level='error')
            return

        curso = queryset.first()
        inscripciones = curso.inscripcion_set.all()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="estudiantes_{curso.nombre}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Nombre de Usuario', 'Nombre', 'Apellido','Email', 'telefono', 'fecha_nacimiento','localidad','dni_numero'])

        for inscripcion in inscripciones:
            writer.writerow([
                inscripcion.usuario.username,
                inscripcion.nombre,
                inscripcion.apellido,
                inscripcion.usuario.email,
                inscripcion.telefono,
                inscripcion.fecha_nacimiento,
                inscripcion.localidad,
                inscripcion.dni_numero


            ])

        return response

    exportar_estudiantes_excel.short_description = "Exportar estudiantes inscritos a Excel"


# =============================================
# ModulosAdmin ACTUALIZADO (con import/export)
# =============================================
@admin.register(Modulos)
class ModulosAdmin(ImportExportModelAdmin):  # <-- Cambio clave aquí
    resource_class = ModulosResource  # <-- Nuevo resource
    
    list_display = (
        'nombre', 
        'instructor', 
        'carga_horaria', 
        'estado_aprobado', 
        'fecha_inicio_modulo'
    )
    search_fields = ('nombre', 'descripcion')
    list_filter = ('estado_aprobado', 'instructor')
    exclude = ('nota',)


class Claseadmin(admin.ModelAdmin):
    list_display = ('curso', 'nombre')
    search_fields = ('curso', 'nombre')


# Personalización para los modelos Nota
class NotaAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'modulo', 'nota', 'fecha_asignacion')
    search_fields = ('estudiante__username', 'modulo__nombre')
    list_filter = ('modulo',)
    list_editable = ('nota',)









try:
    admin.site.unregister(Cursos)
except admin.sites.NotRegistered:
    pass



























admin.site.register(Cursos, CursosAdmin)

admin.site.register(Asistencia, AsistenciaAdmin)
admin.site.register(Clase, Claseadmin)
admin.site.register(Nota, NotaAdmin)
admin.site.register(EstudiantePen,EstudiantepenAdmin)