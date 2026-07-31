from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.urls import reverse
from .models import Cursos, Inscripcion, Modulos, Asistencia, Clase,Nota,EstudiantePen
from .forms import CursosForm, EstudianteForm, InscripcionPenForm, ModulosForm, RegistroCursoForm, ClaseForm, AsistenciaEstudianteForm
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings
import os
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.db.models import Count, Case, When, FloatField
from django.http import JsonResponse

"""********************************************************
                        Vistas CREAR
********************************************************"""
@login_required
def crear_curso(request):
    if request.method == 'POST':
        form = CursosForm(request.POST, instructor=request.user)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.instructor = request.user
            
            # Obtener los días seleccionados y guardarlos como string separado por comas
            dias_seleccionados = form.cleaned_data.get('dias', [])  # Lista de días seleccionados
            curso.dias = ",".join(dias_seleccionados)  # Convierte la lista en un string
            
            curso.save()  # Guarda el curso primero
            form.save_m2m()  # Guarda las relaciones many-to-many
            
            messages.success(request, 'Curso creado con éxito')
            return redirect('user_profile')
        else:
            print("Errores en el formulario:", form.errors)  # Para depuración
    else:
        form = CursosForm(instructor=request.user)

    return render(request, 'cursos/crear_curso.html', {'form': form})

# Vista para crear un módulo
@login_required
def crear_modulo(request):
    if request.method == 'POST':
        form = ModulosForm(request.POST)
        if form.is_valid():
            modulo = form.save(commit=False)
            modulo.instructor = request.user
            modulo.save()
            messages.success(request, 'Módulo creado con éxito')
            return redirect('user_profile')
    else:
        form = ModulosForm()
    return render(request, 'cursos/crear_modulo.html', {'form': form})

# Vista para crear asistencia
@login_required
def crear_asistencia(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    curso = clase.curso

    if not curso.alumnos_inscriptos.exists():
        messages.error(request, 'No hay estudiantes inscritos en este curso.')
        return redirect('detalle_clase', clase_id=clase.id)

    if request.method == 'POST':
        form = AsistenciaEstudianteForm(request.POST, curso=curso, clase=clase)
        if form.is_valid():
            for estudiante in curso.alumnos_inscriptos.all():
                estado = form.cleaned_data.get(f'estado_{estudiante.id}')
                Asistencia.objects.update_or_create(
                clase=clase,
                estudiante=estudiante,
                defaults={
                    'estado': estado,
                    'fecha': form.cleaned_data['fecha'],
                    'curso': curso  # Asegúrate de pasar el curso
                }
            )
            messages.success(request, 'Asistencia registrada con éxito.')
            return redirect('detalle_clase', clase_id=clase.id)
    else:
        form = AsistenciaEstudianteForm(curso=curso, clase=clase)

    return render(request, 'cursos/crear_asistencia.html', {'form': form, 'clase': clase})

# vista para crear clase
def crear_clase(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)

    if request.method == "POST":
        form = ClaseForm(request.POST)
        if form.is_valid():
            clase = form.save(commit=False)  # No guarda aún
            clase.curso = curso  # Asignar el curso
            clase.save()  # Ahora sí guarda
            return redirect("escritorio_instructores")  # Ajusta la redirección según tu app

    else:
        form = ClaseForm(initial={"curso": curso})

    return render(request, "cursos/crear_clase.html", {"form": form, "curso": curso})


#Vista para crear estudiantes PEN
@login_required
def crear_estudiante_pen(request):
    if request.method == 'POST':
        form = EstudianteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ver_estudiantes_pen')
    else:
        form = EstudianteForm()
    return render(request, 'cursos/crear_estudiante.html', {'form': form})


def felicidades(request):
    
    return render(request,'cursos/felicidades.html')

#Crear registro estudiantes en cursos
@login_required
def registro_curso(request, inscripcion_id=None):
    # Modo edición
    if inscripcion_id:
        inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id, usuario=request.user)
        curso = inscripcion.curso
        es_edicion = True
    else:  # Modo creación
        es_edicion = False
        curso_id = request.GET.get('curso_id')
        curso = get_object_or_404(Cursos, id=curso_id)
        
        # Validaciones solo para nuevo registro
        if not curso.inscripcion_abierta:
            messages.error(request, 'Inscripción cerrada para este curso.')
            return redirect('error_inscripcion')

        inscripciones = Inscripcion.objects.filter(usuario=request.user)
        
        if inscripciones.count() >= 2:
            messages.error(request, 'No puedes inscribirte en más de 2 cursos.')
            return redirect('error_inscripcion')

        if inscripciones.count() == 1:
            existing_curso = inscripciones.first().curso
            dias_nuevo = set(curso.dias)
            dias_existente = set(existing_curso.dias)
            common_days = dias_nuevo.intersection(dias_existente)

            if common_days:
                if (curso.horario_inicio and curso.horario_fin and
                    existing_curso.horario_inicio and existing_curso.horario_fin):
                    if not (curso.horario_fin <= existing_curso.horario_inicio or 
                            curso.horario_inicio >= existing_curso.horario_fin):
                        messages.error(request, 'Conflicto de horario con curso existente.')
                        return redirect('error_inscripcion')
                else:
                    messages.error(request, 'Horarios no definidos para validación.')
                    return redirect('error_inscripcion')

    if request.method == 'POST':
        form = RegistroCursoForm(
            request.POST, 
            request.FILES, 
            instance=inscripcion if es_edicion else None,
            user=request.user
        )
        form.instance.curso = curso  # Mantener el curso original en edición

        if form.is_valid():
            inscripcion = form.save(commit=False)
            if not es_edicion:  # Solo asignar usuario en creación
                inscripcion.usuario = request.user
                inscripcion.email = request.user.email
            inscripcion.save()
            
            if not es_edicion:  # Solo agregar a alumnos en creación
                curso.alumnos_inscriptos.add(request.user)
            
            messages.success(request, 'Inscripción guardada exitosamente!')
            return redirect('ver_inscripcion', inscripcion_id=inscripcion.id)

    else:
        form = RegistroCursoForm(
            instance=inscripcion if es_edicion else None,
            user=request.user,
            initial={'curso': curso} if not es_edicion else None
        )

    return render(request, 'cursos/inscribirse.html', {
        'form': form,
        'curso': curso,
        'es_edicion': es_edicion,
        'inscripcion': inscripcion if es_edicion else None
    })
"""********************************************************
                        VISTAS VER- DETALLES
********************************************************"""
@require_http_methods(["GET"])
def detalle_curso(request, curso_id):
    try:
        curso = Cursos.objects.prefetch_related(
            'alumnos_inscriptos', 
            'modulos'
        ).get(id=curso_id)
    except Cursos.DoesNotExist:
        return JsonResponse({'error': 'Curso no encontrado'}, status=404)

    if not request.user.is_authenticated or request.user.profile.rol != 'instructor':
        return JsonResponse({'error': 'Acceso no autorizado'}, status=403)

    # Serialización de campos básicos
    data = {
        'id': curso.id,
        'nombre': curso.nombre,
        'descripcion': curso.descripcion,
        'fecha_inicio': curso.fecha_inicio.strftime('%d/%m/%Y'),
        'fecha_fin': curso.fecha_fin.strftime('%d/%m/%Y'),
        'max_estudiantes': curso.max_estudiantes,
        'grupo_familia': curso.grupo_familia,
        'aprobado': curso.aprobado,
        'vacantes_disponibles': curso.vacantes_disponibles(),
        
    }

    # Serialización de relaciones
    data['instructor'] = {
        'id': curso.instructor.id,
        'username': curso.instructor.username,
        'nombre_completo': curso.instructor.get_full_name(),
        'email': curso.instructor.email
    }

    data['alumnos_inscriptos'] = [{
        'id': alumno.id,
        'username': alumno.username,
        'nombre_completo': alumno.get_full_name(),
        'ultimo_login': alumno.last_login.strftime('%d/%m/%Y %H:%M') if alumno.last_login else None
    } for alumno in curso.alumnos_inscriptos.all()]

    data['modulos'] = [{
        'id': modulo.id,
        'nombre': modulo.nombre,
        'descripcion': modulo.descripcion,
        'estado_aprobado': modulo.estado_aprobado
    } for modulo in curso.modulos.all()]

    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})

@login_required
def ver_estudiantes(request, curso_id):
    """
    Vista para ver los estudiantes inscritos en un curso específico, y su estado de aprobación.
    """
    curso = get_object_or_404(Cursos, id=curso_id)

    # Filtrar los estudiantes inscritos en este curso y su estado de aprobación
    estudiantes = curso.alumnos_inscriptos.all()

    return render(request, 'cursos/ver_estudiantes.html', {
        'curso': curso,
        'estudiantes':estudiantes
    })

# Vista para mostrar detalles de una clase
def detalle_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    asistencias = clase.asistencias.all()
    return render(request, 'cursos/detalle_clase.html', {'clase': clase, 'asistencias': asistencias})

# Vista para mostrar los detalles de un módulo
def detalle_modulo(request, modulo_id):
    
    modulo = get_object_or_404(Modulos, id=modulo_id)
    cursos_asociados = Cursos.objects.filter(modulos=modulo)
    estudiantes = modulo.estudiantes_inscritos()  # Obtener estudiantes inscritos
    print (estudiantes)
    return render(request, 'cursos/detalle_modulo.html', {
        'modulo': modulo,
        'cursos_asociados': cursos_asociados,
        'estudiantes': estudiantes
    })
    
# Vista para mostrar lista de cursos
def lista_cursos(request):
    sede = request.GET.get('sede', None)
    cursos = Cursos.objects.all()
    
    if sede:
        cursos = cursos.filter(lugar=sede)
    
    ubicaciones = {
        'SEDE': {
            'nombre': 'Sede Central - Virrey Del Pino',
            'imagen': 'img/sede.jpg',
            'direccion': 'San Alberto 6363'
        },
        'SUB_SEDE': {
            'nombre': 'Sub Sede - Gregorio de Laferrere',
            'imagen': 'img/subsede.jpg',
            'direccion': 'Ricardo Gutierrez 6170'
        },
        'ANEXO': {
            'nombre': 'Anexo - Rafael Castillo',
            'imagen': 'img/anexo.jpg',
            'direccion': 'Polledo 2060'
        }
    }
    
    return render(request, 'cursos/lista_cursos.html', {
        'cursos': cursos,
        'ubicaciones': ubicaciones,
        'sede_activa': sede
    })

# Vista para ver asistencias de un curso
@login_required 
def ver_asistencia(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    asistencias = Asistencia.objects.filter(clase__curso=curso)
    return render(request, 'cursos/ver_asistencias.html', {'curso': curso, 'asistencias': asistencias})

@login_required
def ver_inscripcion(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id, usuario=request.user)
    return render(request, 'cursos/ver_inscripcion.html', {'inscripcion': inscripcion})

# Vista para mostrar las clases de un curso
@login_required
def ver_clases(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    clases = Clase.objects.filter(curso=curso)
    return render(request, 'cursos/ver_clases.html', {'curso': curso, 'clases': clases})

def listar_modulos(request):
    """
    Vista para listar todos los módulos disponibles.
    """
    modulos = Modulos.objects.all()  # Obtiene todos los módulos de la base de datos
    return render(request, 'cursos/listar_modulos.html', {'modulos': modulos})

def ver_nota(request):
    """ Muestra las notas del alumno logueado """
    estudiante = request.user  # El usuario actual
    notas = Nota.objects.filter(estudiante=estudiante)  # Buscar sus notas

    return render(request, 'cursos/ver_nota.html', {'notas': notas})

@login_required
def ver_notas_instructor(request, curso_id):
    """
    Vista para que el instructor pueda ver las notas de los estudiantes en las clases
    de un curso. Se obtienen las notas de todos los módulos asociados al curso.
    """
    curso = get_object_or_404(Cursos, id=curso_id)
    # Obtener todos los módulos del curso
    modulos = curso.modulos.all()
    # Obtener las notas asociadas a esos módulos
    notas = Nota.objects.filter(modulo__in=modulos)
    
    # Preparamos los datos para enviar en formato JSON
    data = []
    for nota in notas:
        data.append({
            "estudiante": nota.estudiante.get_full_name() or nota.estudiante.username,
            "modulo": nota.modulo.nombre,
            "nota": nota.nota,
        })
    return JsonResponse({"notas": data})


@login_required
def ver_estudiantes_pen(request):
    estudiantes = EstudiantePen.objects.all()
    return render(request, 'cursos/ver_estudiantes_pen.html', {'estudiantes': estudiantes})

"""********************************************************
                        ENDPOINTS JSON
********************************************************"""


@login_required
def obtener_asistencias(request):
    """
    Obtiene las asistencias con posibilidad de filtrar por curso y/o clase
    """
    try:
        curso_id = request.GET.get('curso_id')
        clase_id = request.GET.get('clase_id')
        
        # Base query con prefetch
        asistencias = Asistencia.objects.select_related(
            'clase', 
            'clase__curso', 
            'estudiante'
        )

        # Filtrado por rol
        if not request.user.is_staff:
            if request.user.profile.rol == 'instructor':
                asistencias = asistencias.filter(clase__curso__instructor=request.user)
            elif request.user.profile.rol == 'estudiante':
                asistencias = asistencias.filter(estudiante=request.user)
            else:
                return JsonResponse({'error': 'Acceso no autorizado'}, status=403)

        # Filtros adicionales
        if curso_id:
            asistencias = asistencias.filter(clase__curso_id=curso_id)
            
        if clase_id:
            asistencias = asistencias.filter(clase_id=clase_id)

        # Serialización simplificada
        asistencias_data = []
        for asistencia in asistencias:
            asistencia_data = {
                'estudiante': {
                    'nombre_completo': f"{asistencia.estudiante.first_name} {asistencia.estudiante.last_name}",
                },
                'estado': asistencia.get_estado_display()  # Muestra la versión legible
            }
            asistencias_data.append(asistencia_data)

        return JsonResponse({
            'count': len(asistencias_data),
            'results': asistencias_data
        }, safe=False)

    except Exception as e:
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

def obtener_cursos_json(request):
    # Filtrado según rol: usuario staff (administrativo) ve todos los cursos, si es instructor solo sus cursos
    if request.user.is_staff:
        cursos = Cursos.objects.all()
    elif request.user.profile.rol == 'instructor':
        cursos = Cursos.objects.filter(instructor=request.user)
    else:
        cursos = Cursos.objects.none()

    data = []
    for curso in cursos:
        curso_data = {
            "id": curso.id,
            "nombre": curso.nombre,
            "descripcion": curso.descripcion,
            "fecha_inicio": curso.fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": curso.fecha_fin.strftime("%Y-%m-%d"),
            "max_estudiantes": curso.max_estudiantes,
            "grupo_familia": curso.grupo_familia,
            "aprobado": curso.aprobado,
            "lugar": curso.lugar,
            "inscripcion_abierta": curso.inscripcion_abierta,
            "cursando": curso.cursando,
            "dias": curso.dias_cursada(),
            "horario": curso.horario_formateado(),
            "instructor": {
                "id": curso.instructor.id,
                "nombre": f"{curso.instructor.first_name} {curso.instructor.last_name}",
                "email": curso.instructor.email,
            },
            "alumnos_inscriptos": curso.alumnos_inscriptos_nombres(),
            "alumnos_inscriptos_pen": [pen.nombre for pen in curso.alumnos_inscriptos_pen.all()],
            "modulos": [{
                "id": modulo.id,
                "nombre": modulo.nombre,
                "descripcion": modulo.descripcion,
                "carga_horaria": modulo.carga_horaria,
                "fecha_inicio_modulo": modulo.fecha_inicio_modulo.strftime("%Y-%m-%d"),
                "fecha_fin_modulo": modulo.fecha_fin_modulo.strftime("%Y-%m-%d"),
                "dias": modulo.dias,
                "estado_aprobado": modulo.estado_aprobado,
            } for modulo in curso.modulos.all()],
            "clases": [{
                "id": clase.id,
                "nombre": clase.nombre,
                "descripcion": clase.descripcion,
                "fecha": clase.fecha.strftime("%Y-%m-%d"),
            } for clase in curso.clases.all()],
            "asistencias": [{
                "id": asistencia.id,
                "clase": asistencia.clase.nombre,
                "estudiante": f"{asistencia.estudiante.first_name} {asistencia.estudiante.last_name}",
                "estado": asistencia.estado,
                "fecha": asistencia.fecha.strftime("%Y-%m-%d"),
            } for asistencia in curso.asistencias.all()],
        }
        data.append(curso_data)
    return JsonResponse(data, safe=False)


# En views.py de la app cursos
def obtener_modulos_por_curso_json(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    modulos = curso.modulos.all()
    data = [{"id": modulo.id, "nombre": modulo.nombre} for modulo in modulos]
    return JsonResponse(data, safe=False)

def obtener_estudiantes_curso_json(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    estudiantes = curso.alumnos_inscriptos.all()
    estudiantes_pen = curso.alumnos_inscriptos_pen.all()  # Suponiendo que tienes este related_name

    data = {
        "curso": curso.nombre,
        "curso_id": curso.id,
        "estudiantes": [
            {
                "id": estudiante.id,
                "nombre": estudiante.get_full_name() or estudiante.username,
                "email": estudiante.email,
                "ultimo_login": estudiante.last_login.strftime("%d/%m/%Y %H:%M") if estudiante.last_login else "Nunca"
            }
            for estudiante in estudiantes
        ],
        "estudiantes_pen": [
            {
                "nombre": estudiante.nombre,
                "dni":estudiante.dni
            }
            for estudiante in estudiantes_pen
        ]
    }

    return JsonResponse(data)

def obtener_datos_curso(request, curso_id):
    if request.method == 'GET':
        curso = get_object_or_404(Cursos, id=curso_id)
        
        # Obtener datos del instructor relacionado
        instructor = curso.instructor
        datos_instructor = {
            'id': instructor.id,
            'username': instructor.username,
            'Apellido': f"{instructor.last_name}",
            'email': instructor.email
        }
        
        datos = {
            'id': curso.id,
            'nombre': curso.nombre,
            'instructor': datos_instructor,  # Ahora es un objeto con detalles
            'descripcion': curso.descripcion,
            'fecha_inicio': curso.fecha_inicio.strftime("%d/%m/%Y"),
            'fecha_fin': curso.fecha_fin.strftime("%d/%m/%Y"),
            'max_estudiantes': curso.max_estudiantes,
            'vacantes_disponibles': curso.vacantes_disponibles(),  # Usamos el método del modelo
            'grupo_familia': curso.grupo_familia,
            'modulos': list(curso.modulos.values('id', 'nombre', 'estado_aprobado')),
            'aprobado': curso.aprobado
        }
        return JsonResponse(datos)

@login_required
def obtener_clases(request, curso_id):
    """
    Vista para obtener las clases asociadas a un curso en formato JSON.
    """
    curso = get_object_or_404(Cursos, id=curso_id)
    
    # Obtener todas las clases asociadas al curso
    clases = Clase.objects.filter(curso=curso)
    
    # Crear una lista con los datos de las clases que quieres devolver en formato JSON
    clases_data = []
    for clase in clases:
        clase_data = {
            'id': clase.id,
            'nombre': clase.nombre,
            'fecha': clase.fecha.strftime('%Y-%m-%d'),  # Si la fecha es un campo DateTime
            'descripcion': clase.descripcion,
        }
        clases_data.append(clase_data)
    
    # Devolver las clases en formato JSON
    return JsonResponse({'clases': clases_data})

@login_required
def obtener_email_json(request):
    email_json = {
        'email': request.user.email,
        # Puedes agregar otros campos que necesites
        
    }
    return JsonResponse(email_json)
  
"""********************************************************
                        VISTAS ELIMINAR 
********************************************************"""

def eliminar_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    curso_id = clase.curso.id  # Guarda el ID del curso para redirigir
    clase.delete()
    messages.success(request, "La clase ha sido eliminada exitosamente.")
    return redirect('ver_clases', curso_id=curso_id)


def eliminar_curso(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    
    if request.method == "POST":  # Confirmar que la eliminación es por POST
        curso.delete()
        messages.success(request, "El curso ha sido eliminado exitosamente.")
        return redirect('lista_cursos')  # Cambia 'lista_cursos' por la URL de tu lista de cursos
    
    return render(request, 'cursos/confirmar_eliminar_curso.html', {'curso': curso})

@require_POST
def eliminar_modulo(request, modulo_id):
    try:
        modulo = Modulos.objects.get(id=modulo_id)
        modulo.delete()
        return JsonResponse({
            "success": True,
            "message": f"Módulo {modulo.nombre} eliminado correctamente"
        })
    except Modulos.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Módulo no encontrado"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


def eliminar_estudiante(request, curso_id, estudiante_id):
    curso = get_object_or_404(Cursos, id=curso_id)

    if not request.user.is_staff and request.user != curso.instructor:
        return JsonResponse({
            'success': False,
            'error': "No tienes permiso para eliminar a este estudiante."
        })

    try:
        estudiante_id_int = int(estudiante_id)
        User = get_user_model()
        estudiante = User.objects.get(id=estudiante_id_int)
        Inscripcion.objects.filter(curso=curso, usuario=estudiante).delete()
        curso.alumnos_inscriptos.remove(estudiante)
        mensaje = f"El estudiante {estudiante.get_full_name()} ha sido eliminado del curso."
    except (ValueError, User.DoesNotExist):
        estudiante = get_object_or_404(EstudiantePen, dni=estudiante_id)
        curso.alumnos_inscriptos_pen.remove()
        mensaje = f"El estudiante pendiente {estudiante.nombre} ha sido eliminado del curso."

    return JsonResponse({
        'success': True,
        'message': mensaje
    })


def eliminar_estudiante_pen(request, curso_id, dni):
    curso = get_object_or_404(Cursos, id=curso_id)

    # Verificar permisos: el usuario debe ser staff o el instructor del curso
    if not request.user.is_staff and request.user != curso.instructor:
        return JsonResponse({
            'success': False,
            'error': "No tienes permiso para eliminar a este estudiante."
        })

    # Buscar al estudiante penitenciario usando el dni
    estudiante_pen = get_object_or_404(EstudiantePen, dni=dni)

    # Aquí defines la lógica: si se debe remover de alguna relación ManyToMany o simplemente eliminar el registro.
    # Por ejemplo, eliminamos el registro:
    estudiante_pen.delete()

    return JsonResponse({
        'success': True,
        'message': f"El estudiante penitenciario {estudiante_pen.nombre} ha sido eliminado del curso."
    })


def eliminar_estudiante_pen_curso(request, curso_id, dni):
    curso = get_object_or_404(Cursos, id=curso_id)

    # Verificar permisos: el usuario debe ser staff o el instructor del curso
    if not request.user.is_staff and request.user != curso.instructor:
        return JsonResponse({
            'success': False,
            'error': "No tienes permiso para eliminar a este estudiante del curso."
        })

    # Obtener al estudiante penitenciario usando el dni
    estudiante_pen = get_object_or_404(EstudiantePen, dni=dni)

    # Remover al estudiante del ManyToMany 'alumnos_inscriptos_pen'
    curso.alumnos_inscriptos_pen.remove(estudiante_pen)
    print (curso.alumnos_inscriptos_pen)
    return JsonResponse({
        'success': True,
        'message': f"El estudiante penitenciario {estudiante_pen.nombre} ha sido eliminado del curso."
    })


def eliminar_clase(request, curso_id, clase_id):
    try:
        curso = get_object_or_404(Cursos, id=curso_id)
        clase = get_object_or_404(Clase, id=clase_id, curso=curso)
        clase.delete()
        messages.success(request, "¡Clase eliminada exitosamente!")  # Mensaje de éxito
    except Exception as e:
        messages.error(request, f"Error al eliminar la clase: {str(e)}")  # Mensaje de error
    
    return redirect('escritorio_instructores')  # Redirige a la vista "escritorio-instructores"
    

"""********************************************************
                        VISTAS EDITAR
                          **********************************************"""
@login_required
def editar_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulos, id=modulo_id, instructor=request.user)
    
    if request.method == "POST":
        form = ModulosForm(request.POST, request.FILES, instance=modulo)
        if form.is_valid():
            form.save()
            return JsonResponse({
                "success": True,
                "message": "Módulo actualizado correctamente"
            })
        else:
            # En tu vista editar_modulo
            return JsonResponse({
                "success": False,
                "errors": form.errors.as_json()  # Usa as_json() en lugar de get_json_data()
            }, status=400)
    else:
        # La instancia se pasa para que el formulario se cargue con los valores actuales
        form = ModulosForm(instance=modulo)
        return render(request, "cursos/editar_modulo_form.html", {
            "form": form,
            "modulo": modulo
        })

@login_required
def editar_curso(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    instructor = curso.instructor

    if request.method == "POST":
        form = CursosForm(request.POST, instance=curso, instructor=instructor)
        if form.is_valid():
            curso = form.save()
            
            # Respuesta para AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Cambios guardados exitosamente'
                })
            
            # Redirección normal
            return redirect('editar_curso', curso_id=curso_id)
        
        # Manejo de errores para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data()
            }, status=400)

        return render(request, "cursos/editar_curso_form.html", {"form": form, "curso": curso})

    else:
        form = CursosForm(instance=curso, instructor=instructor)
        return render(request, "cursos/editar_curso_form.html", {"form": form, "curso": curso})
    

@login_required
def editar_asistencia(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    curso = clase.curso

    if not curso.alumnos_inscriptos.exists():
        messages.error(request, 'No hay estudiantes inscritos en este curso.')
        return redirect('detalle_clase', clase_id=clase.id)

    if request.method == 'POST':
        form = AsistenciaEstudianteForm(request.POST, curso=curso, clase=clase)
        if form.is_valid():
            for estudiante in curso.alumnos_inscriptos.all():
                estado = form.cleaned_data.get(f'estado_{estudiante.id}')
                Asistencia.objects.update_or_create(
                    clase=clase,
                    estudiante=estudiante,
                    defaults={
                        'estado': estado,
                        'fecha': form.cleaned_data['fecha'],
                        'curso': curso
                    }
                )
            messages.success(request, 'Asistencia actualizada con éxito.')
            return redirect('detalle_clase', clase_id=clase.id)
    else:
        form = AsistenciaEstudianteForm(curso=curso, clase=clase)
        estudiantes = []
        for estudiante in curso.alumnos_inscriptos.all():
            asistencia = Asistencia.objects.filter(clase=clase, estudiante=estudiante).first()
            estado = asistencia.estado if asistencia else ''
            estudiantes.append({
                'id': estudiante.id,
                'first_name': estudiante.first_name,
                'last_name': estudiante.last_name,
                'estado': estado
            })

    return render(request, 'cursos/editar_asistencia.html', {
        'form': form,
        'clase': clase,
        'estudiantes': estudiantes  # Pasar los estudiantes con su estado al template
    })

"""********************************************************
                        VISTAS GENERALES
********************************************************"""

def gestionar_notas(request, modulo_id):
    modulo = get_object_or_404(Modulos, id=modulo_id)
    curso_asociado = modulo.cursos_asociados.first()

    if not curso_asociado:
        return HttpResponse("Error: El módulo no está asociado a ningún curso.", status=400)

    estudiantes = curso_asociado.alumnos_inscriptos.all()

    if request.method == 'POST':
        for estudiante in estudiantes:
            nota_str = request.POST.get(f'nota_{estudiante.id}', '')  # Obtener la nota como string
            if nota_str:  # Evitar errores si está vacío
                try:
                    nota = float(nota_str)  # Convertir a número
                except ValueError:
                    return HttpResponse("Error: La nota debe ser un número válido.", status=400)

                Nota.objects.update_or_create(
                    estudiante=estudiante,
                    modulo=modulo,
                    defaults={'nota': nota}  # Guardar como número
                )

        return HttpResponseRedirect(reverse('detalle_modulo', args=[modulo.id]))

    return render(request, 'cursos/gestionar_nota.html', {
        'modulo': modulo,
        'estudiantes': estudiantes,
    })


@login_required
def mis_inscripciones(request):
    inscripciones = Inscripcion.objects.filter(usuario=request.user)
    return render(request, 'cursos/mis_inscripciones.html', {'inscripciones': inscripciones})

@login_required
def inscribir_curso_pen(request, estudiante_id):
    estudiante = get_object_or_404(EstudiantePen, id=estudiante_id)
    if request.method == 'POST':
        form = InscripcionPenForm(request.POST)
        if form.is_valid():
            inscripcion = form.save(commit=False)
            inscripcion.estudiante = estudiante
            # El campo 'estado' se establece automáticamente como "pendiente"
            inscripcion.save()
            return redirect('ver_estudiantes_pen')
    else:
        form = InscripcionPenForm()
    return render(request, 'cursos/inscribir_curso.html', {
        'form': form,
        'estudiante': estudiante
    })


def exportar_inscripcion_pdf(request, inscripcion_id):
    inscripcion = Inscripcion.objects.get(id=inscripcion_id)

    # Obtener la URL de la imagen cargada
    imagen_url = os.path.join(settings.MEDIA_ROOT, str(inscripcion.imagen))

    # Pasar los datos al template
    context = {
        'inscripcion': inscripcion,
        'imagen_url': imagen_url,  # Ruta absoluta en el servidor
    }
    
    template_path = 'admin/pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)

    # Crear la respuesta HTTP con el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="inscripcion_{inscripcion.id}.pdf"'

    # Generar el PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error al generar el PDF", status=500)

    return response


def escritorio_instructores_vista(request):
    # Verificar si es instructor
    if request.user.profile.rol == 'instructor':
        cursos = Cursos.objects.filter(instructor=request.user)
        modulos = Modulos.objects.filter(instructor=request.user)
        # Crear una instancia del formulario
        form = CursosForm()
    else:
        # Si el usuario no es instructor, redirigir o mostrar un mensaje
        cursos = []
        modulos = []
        form = None
    
    return render(request, 'cursos/escritorio_instructores.html', {
        'cursos': cursos,
        'modulos': modulos,
        'form': form,
    })


def error_inscripcion(request):
    return render(request, 'cursos/error_inscripcion.html')

def inscripciones_view(request):
    curso_id = request.GET.get('curso')
    if (curso_id):
        inscripciones = Inscripcion.objects.filter(curso__id=curso_id)
    else:
        inscripciones = Inscripcion.objects.all()
    
    context = {
        'inscripciones': inscripciones,
    }
    return render(request, 'cursos/inscripciones_list.html', context)

@login_required
def escritorio_directivo(request):
    if not request.user.is_staff:
        return redirect('escritorio_instructores')
    return render(request, 'cursos/escritorio_directivo.html')



# views.py


@login_required
def promedio_asistencias(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    
    # Obtener todos los estudiantes (regulares y PEN)
    estudiantes_regulares = curso.alumnos_inscriptos.all()
    estudiantes_pen = curso.alumnos_inscriptos_pen.all()
    
    # Calcular promedios para estudiantes regulares
    promedios = []
    for estudiante in estudiantes_regulares:
        total_clases = Asistencia.objects.filter(curso=curso, estudiante=estudiante).count()
        presentes = Asistencia.objects.filter(curso=curso, estudiante=estudiante, estado='presente').count()
        
        promedio = (presentes / total_clases * 100) if total_clases > 0 else 0
        promedios.append({
            'nombre': f"{estudiante.first_name} {estudiante.last_name}",
            'dni': estudiante.dni_numero if hasattr(estudiante, 'dni_numero') else 'N/A',
            'promedio': round(promedio, 2),
            'tipo': 'Regular'
        })

    # Calcular promedios para estudiantes PEN
    for estudiante_pen in estudiantes_pen:
        total_clases = Asistencia.objects.filter(curso=curso, estudiante_pen=estudiante_pen).count()
        presentes = Asistencia.objects.filter(curso=curso, estudiante_pen=estudiante_pen, estado='presente').count()
        
        promedio = (presentes / total_clases * 100) if total_clases > 0 else 0
        promedios.append({
            'nombre': estudiante_pen.nombre,
            'dni': estudiante_pen.dni,
            'promedio': round(promedio, 2),
            'tipo': 'PEN'
        })

    return JsonResponse({'promedios': promedios})