from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import Cursos, Inscripcion, Modulos, Asistencia, Clase, Nota, EstudiantePen, EstudiantesEliminados
from .forms import CursosForm, EstudianteForm, InscripcionPenForm, ModulosForm, RegistroCursoForm, ClaseForm, AsistenciaEstudianteForm
from django.contrib.auth import get_user_model, login, authenticate
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from django.conf import settings
import os
from django.contrib.auth.models import User
from django.db.models import Count
from cuentas.models import Contacto, Profile
from django.views.decorators.csrf import csrf_exempt
from calendar import monthrange
from django.utils.timezone import datetime
from datetime import datetime
from .choices import LOCALIDADES_POR_PARTIDO
from django.core.cache import cache
import json
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
from cuentas.utils import extraer_dni_ocr
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
            
            curso.save()  # Guarda el curso primero
            form.save_m2m()  # Guarda las relaciones many-to-many
            
            messages.success(request, 'Curso creado con éxito')
            return redirect('escritorio_instructores')
        else:
            print("Errores en el formulario:", form.errors)  # Para depuración
    else:
        form = CursosForm(instructor=request.user)

    return render(request, 'cursos/crear_curso.html', {'form': form})

# Vista para crear un módulo
@login_required
def crear_modulo(request):
    if request.method == 'POST':
        # AGREGAR request.FILES AQUÍ
        form = ModulosForm(request.POST, request.FILES) 
        
        if form.is_valid():
            modulo = form.save(commit=False)
            modulo.instructor = request.user
            modulo.save()
            messages.success(request, 'Módulo creado con éxito')
            return redirect('escritorio_instructores')
        else:
            # ESTO ES IMPORTANTE PARA DEPURAR
            # Si el form no es válido, imprime los errores en la consola
            print("Errores del formulario:", form.errors)
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

    # Obtener los estudiantes con sus nombres completos
    estudiantes = [
        {
            'id': estudiante.id,
            'nombre_completo': f"{estudiante.first_name} {estudiante.last_name}"
        }
        for estudiante in curso.alumnos_inscriptos.all()
    ]

    return render(request, 'cursos/crear_asistencia.html', {
        'form': form,
        'clase': clase,
        'estudiantes': estudiantes  # Pasar los nombres completos al template
    })

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



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
# Asegúrate de importar tu formulario y modelos
from .forms import RegistroCursoForm
from .models import Cursos, Inscripcion
# IMPORTAR EL DICCIONARIO
from .choices import LOCALIDADES_POR_PARTIDO 

@login_required
def registro_curso(request, inscripcion_id=None):
    # Modo edición de una inscripción existente
    if inscripcion_id:
        inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id, usuario=request.user)
        curso = inscripcion.curso
        es_edicion = True
    # Modo nueva inscripción
    else:  
        es_edicion = False
        curso_id = request.GET.get('curso_id')
        curso = get_object_or_404(Cursos, id=curso_id)
        cantidad_estudiantes = curso.alumnos_inscriptos.count()
        # 1. Validar si el curso acepta inscripciones
        if cantidad_estudiantes >= curso.max_estudiantes:
            messages.error(request, 'El curso está lleno.')
            return redirect('error_inscripcion')
        if not curso.inscripcion_abierta:
            messages.error(request, 'Inscripciones cerradas para este curso.')
            return redirect('error_inscripcion')

        # 2. Obtener SOLO cursos activos (cursando=True) del usuario
        cursos_activos = Cursos.objects.filter(
            alumnos_inscriptos=request.user,
            cursando=True  # Solo considerar cursos en progreso
        )

        # 3. Validar límite de 2 cursos activos
        if cursos_activos.count() >= 2:
            messages.error(request, 'Límite: 2 cursos activos simultáneamente.')
            return redirect('error_inscripcion')

        # 4. Validar conflicto horario SOLO si tiene cursos activos
        if cursos_activos.exists():
            for curso_activo in cursos_activos:
                # 4.1 Comparar días
                dias_comunes = set(curso.dias) & set(curso_activo.dias)
                if not dias_comunes:
                    continue  # No hay días comunes, no hay conflicto
                
                # 4.2 Validar horarios si ambos tienen definidos
                if all([
                    curso.horario_inicio,
                    curso.horario_fin,
                    curso_activo.horario_inicio,
                    curso_activo.horario_fin
                ]):
                    # Detectar superposición horaria
                    if (curso.horario_inicio < curso_activo.horario_fin and
                        curso.horario_fin > curso_activo.horario_inicio):
                        messages.error(request, f'Conflicto de horario con {curso_activo.nombre}')
                        return redirect('error_inscripcion')

    # Lógica común para guardar el formulario
    if request.method == 'POST':
        print(f"\n[DEBUG-VIEW] --- POST Recibido para curso: {curso.nombre} ---")
        form = RegistroCursoForm(
            request.POST, 
            request.FILES, 
            instance=inscripcion if es_edicion else None,
            user=request.user
        )
        print(f"[DEBUG-VIEW] Formulario inicializado. Procesando is_valid()...")
        if form.is_valid():
            print(f"DEBUG: Formulario válido para usuario {request.user.username} en curso {curso.nombre}")
            try:
                inscripcion = form.save(commit=False)
                
                # Asignar el usuario y email antes de guardar
                if not es_edicion:
                    inscripcion.usuario = request.user
                    inscripcion.curso = curso  # ¡IMPORTANTE! Asignar el curso
                    inscripcion.email = request.user.email
                    
                    # Verificar que el usuario no esté ya inscripto en este curso
                    if Inscripcion.objects.filter(usuario=request.user, curso=curso).exists():
                        print(f"DEBUG: Usuario {request.user.username} ya está inscripto en {curso.nombre}")
                        messages.error(request, 'Ya estás inscripto en este curso.')
                        return redirect('lista_cursos')
                    
                    print(f"DEBUG: Agregando {request.user.username} a alumnos_inscriptos de {curso.nombre}")
                    curso.alumnos_inscriptos.add(request.user)  # Asignar al curso
                else:
                    # En modo edición, asegurarse de mantener el usuario y email
                    inscripcion.email = request.user.email
                
                # Guardar la inscripción
                print(f"[DEBUG-VIEW] Intentando guardar inscripción final en la DB...")
                inscripcion.save()
                print(f"[DEBUG-VIEW] ✅ Inscripción guardada con éxito. ID: {inscripcion.id}")
                
                messages.success(request, 'Pre-¡Inscripción exitosa!')
                return redirect('ver_inscripcion', inscripcion_id=inscripcion.id)
                
            except Exception as e:
                print(f"DEBUG: ERROR al guardar inscripción: {str(e)}")
                messages.error(request, f'Error al guardar la inscripción: {str(e)}')
                # Si hay error, mantener los datos del formulario
                return render(request, 'cursos/inscribirse.html', {
                    'form': form,
                    'curso': curso,
                    'es_edicion': es_edicion,
                    'inscripcion': inscripcion if es_edicion else None,
                    # CORRECTO: Pasar el diccionario puro
                    'localidades_por_partido': LOCALIDADES_POR_PARTIDO,
                })
        else:
            print(f"[DEBUG-VIEW] ❌ Formulario INVÁLIDO. Errores: {form.errors.as_json()}")
            # Si el formulario no es válido, renderizar con errores
            return render(request, 'cursos/inscribirse.html', {
                    'form': form,
                    'curso': curso,
                    'es_edicion': es_edicion,
                    'inscripcion': inscripcion if es_edicion else None,
                    # CORRECTO: Pasar el diccionario puro
                    'localidades_por_partido': LOCALIDADES_POR_PARTIDO,
                })

    else:
        # GET Request
        form = RegistroCursoForm(
            instance=inscripcion if es_edicion else None,
            user=request.user,
            initial={'curso': curso} if not es_edicion else None
        )
        
    # Lógica del popup de advertencia (máximo 3 visualizaciones por usuario)
    cache_key = f'popup_inscripcion_visto_{request.user.id}'
    contador_vistas = cache.get(cache_key, 0)
    mostrar_popup = contador_vistas < 3
    
    # Si se debe mostrar, incrementar contador
    if mostrar_popup:
        cache.set(cache_key, contador_vistas + 1, timeout=2592000)  # 30 días en segundos
    
    # Renderizar el formulario con los valores iniciales  
    return render(request, 'cursos/inscribirse.html', {
        'form': form,
        'curso': curso,
        'es_edicion': es_edicion,
        'inscripcion': inscripcion if es_edicion else None,
        # ==========================================================
        # CORRECCIÓN AQUÍ: NO USAR json.dumps(). 
        # Pasar el diccionario de Python directamente.
        # ==========================================================
        'localidades_por_partido': LOCALIDADES_POR_PARTIDO, 
        'mostrar_popup': mostrar_popup
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
    
    # Obtener estudiantes regulares de TODOS los cursos asociados al módulo
    estudiantes_regulares = User.objects.filter(
        cursos_inscriptos__in=cursos_asociados
    ).distinct()
    
    # Obtener estudiantes Pen de TODOS los cursos asociados al módulo
    estudiantes_pen = EstudiantePen.objects.filter(
        cursos_inscriptos_pen__in=cursos_asociados
    ).distinct()
    
    return render(request, 'cursos/detalle_modulo.html', {
        'modulo': modulo,
        'cursos_asociados': cursos_asociados,
        'estudiantes_regulares': estudiantes_regulares,
        'estudiantes_pen': estudiantes_pen
    })
# Vista para mostrar lista de cursos
def lista_cursos(request):
    # 1. Capturamos los filtros (si no hay año, asumimos 2026 por defecto)
    sede = request.GET.get('sede', '')
    anio_seleccionado = request.GET.get('anio', '2026') 
    
    # 2. Obtenemos todos los cursos base
    cursos = Cursos.objects.all()

    # 3. Aplicamos filtro de año (Ciclo Lectivo)
    # Si un curso empieza en 2025, pertenece al ciclo 2025 aunque termine en 2026
    if anio_seleccionado:
        cursos = cursos.filter(fecha_inicio__year=anio_seleccionado)

    # 4. Aplicamos filtro de sede si existe
    if sede:
        cursos = cursos.filter(lugar=sede)
    
    # Datos estáticos de las sedes
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
        'sede_activa': sede,
        'anio_activo': anio_seleccionado # Pasamos el año para pintar el botón activo
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

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        base_template = 'cursos/base_modal.html'
    else:
        base_template = 'cuentas/base.html'

    return render(request, 'cursos/ver_clases.html', {
        'curso': curso, 
        'clases': clases,
        'base_template': base_template
    })

def listar_modulos(request):
    """
    Vista para listar todos los módulos disponibles.
    """
    modulos = Modulos.objects.all()  # Obtiene todos los módulos de la base de datos
    return render(request, 'cursos/listar_modulos.html', {'modulos': modulos})

@login_required
def ver_detalle_inscripcion(request, inscripcion_id):
    """
    Vista para que directivos/instructores vean el detalle de una inscripción.
    """
    # Verificar permisos (staff o instructor)
    if not (request.user.is_staff or request.user.profile.rol == 'instructor'):
        messages.error(request, 'No tienes permisos para ver esta inscripción.')
        return redirect('home')

    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    return render(request, 'cursos/ver_inscripcion_directivo.html', {'inscripcion': inscripcion})

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
def ver_notas_modulo(request, modulo_id):
    """
    Vista para obtener las notas de todos los estudiantes en un módulo específico.
    Retorna JSON con la lista de estudiantes y sus respectivas notas.
    """
    modulo = get_object_or_404(Modulos, id=modulo_id)
    
    # Verificar que el usuario es el instructor del módulo o es staff
    if not (request.user == modulo.instructor or request.user.is_staff):
        return JsonResponse({'error': 'No tienes permiso para ver estas notas'}, status=403)
    
    # Obtener todos los cursos asociados al módulo
    cursos = modulo.cursos_asociados.all()
    
    # Obtener todos los estudiantes regulares inscritos en esos cursos
    estudiantes_regulares = User.objects.filter(
        cursos_inscriptos__in=cursos
    ).distinct()
    
    # Obtener todos los estudiantes PEN inscritos en esos cursos
    estudiantes_pen = EstudiantePen.objects.filter(
        cursos_inscriptos_pen__in=cursos
    ).distinct()
    
    estudiantes_data = []
    
    # Procesar estudiantes regulares
    for estudiante in estudiantes_regulares:
        try:
            nota_obj = Nota.objects.get(estudiante=estudiante, modulo=modulo)
            nota_valor = nota_obj.nota
        except Nota.DoesNotExist:
            nota_valor = None
        
        # Intentar obtener el DNI de la inscripción
        dni = None
        inscripcion = Inscripcion.objects.filter(
            usuario=estudiante, 
            curso__modulos=modulo
        ).first()
        if inscripcion:
            dni = inscripcion.dni
        
        estudiantes_data.append({
            'nombre_completo': estudiante.get_full_name() or estudiante.username,
            'dni': dni,
            'nota': nota_valor,
            'es_pen': False
        })
    
    # Procesar estudiantes PEN
    for estudiante_pen in estudiantes_pen:
        # Para estudiantes PEN, verificar si hay nota (si implementaste el soporte)
        # Por ahora, asumimos que no tienen notas o que se manejan de forma diferente
        estudiantes_data.append({
            'nombre_completo': estudiante_pen.nombre,
            'dni': estudiante_pen.dni,
            'nota': None,  # Los estudiantes PEN pueden no tener notas en el sistema
            'es_pen': True
        })
    
    return JsonResponse({
        'modulo': modulo.nombre,
        'estudiantes': estudiantes_data
    })


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
    # 1. Mantenemos la optimización de consultas para evitar lentitud y cuelgues
    cursos_base = Cursos.objects.select_related('instructor').prefetch_related(
        'alumnos_inscriptos',
        'alumnos_inscriptos_pen',
        'modulos',
        'clases',
        'asistencias__clase',
        'asistencias__estudiante'
    )

    if request.user.is_staff:
        cursos = cursos_base.all()
    elif request.user.profile.rol == 'instructor':
        cursos = cursos_base.filter(instructor=request.user)
    else:
        cursos = Cursos.objects.none()

    data = []
    for curso in cursos:
        # 2. Manejo seguro de las asistencias (Evita el Error 500)
        asistencias_data = []
        for asistencia in curso.asistencias.all():
            
            # Verificamos de forma segura si existe el estudiante regular
            if getattr(asistencia, 'estudiante', None):
                nombre_estudiante = f"{asistencia.estudiante.first_name} {asistencia.estudiante.last_name}"
            # Si no, verificamos si es un estudiante PEN (si tienes esa relación configurada)
            elif getattr(asistencia, 'estudiante_pen', None):
                nombre_estudiante = f"{asistencia.estudiante_pen.nombre} (PEN)"
            else:
                nombre_estudiante = "Desconocido"

            asistencias_data.append({
                "id": asistencia.id,
                # También verificamos que la clase no sea nula por seguridad
                "clase_id": asistencia.clase.id if getattr(asistencia, 'clase', None) else None,
                "clase": asistencia.clase.nombre if getattr(asistencia, 'clase', None) else "Sin clase",
                "estudiante": nombre_estudiante,
                "estado": asistencia.estado,
                "fecha": asistencia.fecha.strftime("%Y-%m-%d") if asistencia.fecha else "",
            })

        curso_data = {
            "lugar": curso.lugar,
            "id": curso.id,
            "nombre": curso.nombre,
            "descripcion": curso.descripcion,
            "fecha_inicio": curso.fecha_inicio.strftime("%Y-%m-%d") if curso.fecha_inicio else "",
            "fecha_fin": curso.fecha_fin.strftime("%Y-%m-%d") if curso.fecha_fin else "",
            "max_estudiantes": curso.max_estudiantes,
            "grupo_familia": curso.grupo_familia,
            "aprobado": curso.aprobado,
            "inscripcion_abierta": curso.inscripcion_abierta,
            "cursando": curso.cursando,
            "dias": curso.dias_cursada(),
            "horario": curso.horario_formateado(),
            "instructor": {
                "id": curso.instructor.id if curso.instructor else None,
                "nombre": f"{curso.instructor.first_name} {curso.instructor.last_name}" if curso.instructor else "Sin asignar",
                "email": curso.instructor.email if curso.instructor else "",
            },
            "alumnos_inscriptos": curso.alumnos_inscriptos_nombres(),
            "alumnos_inscriptos_pen": [pen.nombre for pen in curso.alumnos_inscriptos_pen.all()],
            "modulos": [{
                "id": modulo.id,
                "nombre": modulo.nombre,
                "descripcion": modulo.descripcion,
                "carga_horaria": modulo.carga_horaria,
                "fecha_inicio_modulo": modulo.fecha_inicio_modulo.strftime("%Y-%m-%d") if modulo.fecha_inicio_modulo else "",
                "fecha_fin_modulo": modulo.fecha_fin_modulo.strftime("%Y-%m-%d") if modulo.fecha_fin_modulo else "",
                "dias": modulo.dias,
                "estado_aprobado": modulo.estado_aprobado,
            } for modulo in curso.modulos.all()],
            "clases": [{
                "id": clase.id,
                "nombre": clase.nombre,
                "descripcion": clase.descripcion,
                "fecha": clase.fecha.strftime("%Y-%m-%d") if clase.fecha else "",
            } for clase in curso.clases.all()],
            
            # Insertamos la lista de asistencias que preparamos arriba
            "asistencias": asistencias_data,
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
    estudiantes_pen = curso.alumnos_inscriptos_pen.all()

    data = {
        "curso": curso.nombre,
        "curso_id": curso.id,
        "estudiantes": [
            {
                "id": estudiante.id,
                "nombre": estudiante.get_full_name() or estudiante.username,
                "email": estudiante.email,
                "telefono": Inscripcion.objects.filter(curso=curso, usuario=estudiante).values_list('telefono', flat=True).first() or 'No disponible',
                "ultimo_login": estudiante.last_login.strftime("%d/%m/%Y %H:%M") if estudiante.last_login else "Nunca",
                "inscripcion_id": Inscripcion.objects.filter(curso=curso, usuario=estudiante).values_list('id', flat=True).first(),
                "pago_contribucion": Inscripcion.objects.filter(curso=curso, usuario=estudiante).values_list('pago_contribucion', flat=True).first(),
                "inscripcion_fisica": Inscripcion.objects.filter(curso=curso, usuario=estudiante).values_list('inscripcion_fisica', flat=True).first(),
                "entrega_certificado": Inscripcion.objects.filter(curso=curso, usuario=estudiante).values_list('entrega_certificado', flat=True).first()
            }
            for estudiante in estudiantes
        ],
        "estudiantes_pen": [
            {
                "nombre": estudiante.nombre,
                "dni": estudiante.dni
            }
            for estudiante in estudiantes_pen
        ]
    }

    return JsonResponse(data)

def obtener_estudiantes_eliminados_json(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    eliminaciones = EstudiantesEliminados.objects.filter(curso=curso)

    data = {
        "curso": curso.nombre,
        "curso_id": curso.id,
        "estudiantes_eliminados": [
            {
                "id": elim.estudiante.id,
                "nombre": elim.estudiante.get_full_name() or elim.estudiante.username,
                "email": elim.estudiante.email,
                "instructor": elim.instructor.get_full_name() or elim.instructor.username,
                "fecha": elim.fecha_eliminacion.strftime("%Y-%m-%d %H:%M"),
                "motivo": elim.motivo
            }
            for elim in eliminaciones
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
            'grupo_familia': curso.grupo_familia,
            'dias': curso.dias_cursada(),
            'horario': curso.horario_formateado(),
            'fecha_creacion': curso.fecha_creacion.strftime("%d/%m/%Y") if curso.fecha_creacion else "N/A",
            # calculamos el progreso de calificación
            'modulos': [
                {
                    'id': m.id,
                    'nombre': m.nombre,
                    'estado_aprobado': m.estado_aprobado,
                    'total_estudiantes': curso.alumnos_inscriptos.count(),
                    'estudiantes_con_nota': Nota.objects.filter(
                        modulo=m, 
                        estudiante__in=curso.alumnos_inscriptos.all()
                    ).count()
                }
                for m in curso.modulos.all()
            ],
            'aprobado': curso.aprobado
        }
        return JsonResponse(datos)

@login_required
def obtener_datos_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulos, id=modulo_id)
    
    # Obtener cursos que contienen este módulo para contextualizar
    cursos = modulo.cursos_asociados.all()
    nombres_cursos = [c.nombre for c in cursos]
    
    # Verificar si el usuario es el instructor del módulo o staff
    if not (request.user == modulo.instructor or request.user.is_staff):
         return JsonResponse({'error': 'No tienes permiso para ver este módulo'}, status=403)

    # Calcular datos de alumnos
    estudiantes_regulares = User.objects.filter(cursos_inscriptos__in=cursos).distinct()
    total_estudiantes = estudiantes_regulares.count()
    estudiantes_con_nota = Nota.objects.filter(modulo=modulo, estudiante__in=estudiantes_regulares).count()

    datos = {
        'id': modulo.id,
        'nombre': modulo.nombre,
        'descripcion': modulo.descripcion,
        'carga_horaria': modulo.carga_horaria,
        'fecha_inicio': modulo.fecha_inicio_modulo.strftime("%d/%m/%Y"),
        'fecha_fin': modulo.fecha_fin_modulo.strftime("%d/%m/%Y"),
        'estado_aprobado': modulo.estado_aprobado,
        'recursos_url': modulo.recursos.url if modulo.recursos else None,
        'cursos_asociados': nombres_cursos,
        'total_estudiantes': total_estudiantes,
        'estudiantes_con_nota': estudiantes_con_nota,
        'instructor': {
            'id': modulo.instructor.id,
            'nombre': f"{modulo.instructor.first_name} {modulo.instructor.last_name}",
            'email': modulo.instructor.email
        }
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

@login_required
def obtener_total_estudiantes_json(request):
    """
    Endpoint para obtener la cantidad total de estudiantes inscritos.
    """
    total_estudiantes = Inscripcion.objects.aggregate(total=Count('id'))['total']
    return JsonResponse({'total_estudiantes': total_estudiantes})
  
@login_required
def obtener_total_mensajes_json(request):
    """
    Endpoint para obtener la cantidad total de mensajes recibidos.
    """
    total_mensajes = Contacto.objects.count()
    return JsonResponse({'total_mensajes': total_mensajes})

@login_required
def obtener_mensajes_json(request):
    mensajes = Contacto.objects.all().order_by('-fecha')
    data = [{'id': mensaje.id, 'nombre': mensaje.nombre, 'email': mensaje.email, 'mensaje': mensaje.mensaje} for mensaje in mensajes]
    return JsonResponse({'mensajes': data})

@login_required
def obtener_conversacion(request, mensaje_id):
    mensaje = get_object_or_404(Contacto, id=mensaje_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Verificar si es una solicitud AJAX
        data = {
            'id': mensaje.id,
            'nombre': mensaje.nombre,
            'email': mensaje.email,
            'mensaje': mensaje.mensaje,
            'respuesta': mensaje.respuesta  # Incluir la respuesta
        }
        return JsonResponse(data)
    return render(request, 'cursos/ver_mensaje.html', {'mensaje': mensaje})

@csrf_exempt
@login_required
def responder_mensaje(request, mensaje_id):
    if request.method == 'POST':
        mensaje = get_object_or_404(Contacto, id=mensaje_id)
        respuesta = request.POST.get('respuesta', '')
        mensaje.respuesta = respuesta
        mensaje.save()
        return JsonResponse({'success': True, 'message': 'Respuesta enviada con éxito.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

@login_required
@require_POST
def eliminar_conversacion(request, mensaje_id):
    """
    Vista para eliminar una conversación (mensaje).
    """
    mensaje = get_object_or_404(Contacto, id=mensaje_id)
    mensaje.delete()
    return JsonResponse({'success': True, 'message': 'Mensaje eliminado con éxito.'})

def obtener_inscripciones_curso_json(request, curso_id):
    inscripciones = Inscripcion.objects.filter(curso_id=curso_id).select_related('usuario')
    data = {
        'inscripciones': [
            {
                'estudiante': {
                    'nombre': f"{inscripcion.usuario.first_name} {inscripcion.usuario.last_name}",
                    'email': inscripcion.usuario.email,
                    'telefono': inscripcion.telefono,
                    'direccion': inscripcion.direccion,
                    'fecha_nacimiento': inscripcion.fecha_nacimiento,
                    'dni': inscripcion.dni_numero,
                    'dni_frente': inscripcion.dni_frente.url,
                    'dni_reverso': inscripcion.dni_reverso.url,
                    'analitico_primaria': inscripcion.analitico_primaria.url if inscripcion.analitico_primaria else None,
                    'analitico_primaria_dorso': inscripcion.analitico_primaria_dorso.url if inscripcion.analitico_primaria_dorso else None,


                },
                'estado': 'Aprobado' if inscripcion.curso.aprobado else 'Pendiente',
            }
            for inscripcion in inscripciones
        ]
    }
    return JsonResponse(data)

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


def registro_estudiante_eliminado(instructor, estudiante, curso, motivo):
    """
    Función auxiliar para guardar el registro de un estudiante eliminado.
    """
    EstudiantesEliminados.objects.create(
        instructor=instructor,
        estudiante=estudiante,
        curso=curso,
        motivo=motivo
    )

def eliminar_estudiante(request, curso_id, estudiante_id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

    curso = get_object_or_404(Cursos, id=curso_id)

    if not request.user.is_staff and request.user != curso.instructor:
        return JsonResponse({
            'success': False,
            'error': "No tienes permiso para eliminar a este estudiante."
        })

    # Extraer el motivo del cuerpo JSON
    try:
        data = json.loads(request.body)
        motivo = data.get('motivo', '').strip()
    except json.JSONDecodeError:
        motivo = ''

    if not motivo:
        return JsonResponse({
            'success': False,
            'error': "Debe proporcionar un motivo para eliminar al estudiante."
        })

    try:
        estudiante_id_int = int(estudiante_id)
        User = get_user_model()
        estudiante = User.objects.get(id=estudiante_id_int)
        
        # Guardamos el registro antes de borrar las relaciones
        registro_estudiante_eliminado(request.user, estudiante, curso, motivo)
        
        Inscripcion.objects.filter(curso=curso, usuario=estudiante).delete()
        curso.alumnos_inscriptos.remove(estudiante)
        mensaje = f"El estudiante {estudiante.get_full_name()} ha sido eliminado del curso."
    except (ValueError, User.DoesNotExist):
        estudiante = get_object_or_404(EstudiantePen, dni=estudiante_id)
        # Nota: La lógica actual de EstudiantesEliminados requiere un modelo User para 'estudiante', 
        # así que para los PEN habría que adaptar el modelo (por ejemplo usando GenericForeignKey)
        # Por ahora se saltará el registro si es PEN como el usuario indicó "solamente estudiantes regulares".
        curso.alumnos_inscriptos_pen.remove(estudiante)
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
            return JsonResponse({"success": True, "message": "Módulo actualizado correctamente."})
            
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

    estudiantes = []
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
            # Si el form no es válido, igual preparo 'estudiantes' para mostrar el form con errores
            for estudiante in curso.alumnos_inscriptos.all():
                asistencia = Asistencia.objects.filter(clase=clase, estudiante=estudiante).first()
                estado = asistencia.estado if asistencia else ''  # Puede ser 'presente', 'ausente', o 'media_falta'
                estudiantes.append({
                    'id': estudiante.id,
                    'first_name': estudiante.first_name,
                    'last_name': estudiante.last_name,
                    'estado': estado
                })
    else:
        form = AsistenciaEstudianteForm(curso=curso, clase=clase)
        for estudiante in curso.alumnos_inscriptos.all():
            asistencia = Asistencia.objects.filter(clase=clase, estudiante=estudiante).first()
            estado = asistencia.estado if asistencia else ''  # Puede ser 'presente', 'ausente', o 'media_falta'
            estudiantes.append({
                'id': estudiante.id,
                'first_name': estudiante.first_name,
                'last_name': estudiante.last_name,
                'estado': estado
            })

    return render(request, 'cursos/editar_asistencia.html', {
        'form': form,
        'clase': clase,
        'estudiantes': estudiantes
    })

"""********************************************************
                        VISTAS GENERALES
********************************************************"""

def gestionar_notas(request, modulo_id):
    modulo = get_object_or_404(Modulos, id=modulo_id)
    # Obtener cursos que contienen este módulo para contextualizar
    cursos = modulo.cursos_asociados.all()
    if not cursos.exists():
         return HttpResponse("Error: El módulo no está asociado a ningún curso.", status=400)

    # Obtener todos los estudiantes de todos los cursos asociados al módulo
    estudiantes_queryset = User.objects.filter(cursos_inscriptos__in=cursos).distinct()
    
    # Convertir a lista para evitar que se re-evalúe el QuerySet y se pierdan los atributos .nota
    estudiantes = list(estudiantes_queryset)
    
    # Obtener notas existentes
    notas_existentes = Nota.objects.filter(modulo=modulo, estudiante__in=estudiantes_queryset)
    notas_dict = {nota.estudiante.id: nota.nota for nota in notas_existentes}

    # Adjuntar nota a cada estudiante en la lista
    for estudiante in estudiantes:
        estudiante.nota = notas_dict.get(estudiante.id)

    if request.method == 'POST':
        for estudiante in estudiantes:
            nota_str = request.POST.get(f'nota_{estudiante.id}', '')  # Obtener la nota como string
            
            # Si el campo está vacío, verificamos si existe nota y la borramos
            if not nota_str:
                Nota.objects.filter(estudiante=estudiante, modulo=modulo).delete()
                continue
                
            try:
                nota = float(nota_str)  # Convertir a número
                
                # Validar rango de notas (opcional pero recomendado)
                if not (0 <= nota <= 100):
                     # Podríamos agregar error aquí, o simplemente ignorar
                     pass
                     
                Nota.objects.update_or_create(
                    estudiante=estudiante,
                    modulo=modulo,
                    defaults={'nota': nota}  # Guardar como número
                )
            except ValueError:
                # Si no es un número válido, ignoramos o manejamos error
                pass

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
    # Contar la cantidad total de estudiantes inscriptos en todos los cursos
    cantidad_estudiantes = User.objects.filter(cursos_inscriptos__isnull=False).distinct().count()
    
    # Contar inscripciones para el ciclo lectivo 2026
    inscripciones_2026 = Inscripcion.objects.filter(curso__fecha_inicio__year=2026).count()

    context={
        'cantidad_estudiantes':cantidad_estudiantes,
        'inscripciones_2026': inscripciones_2026,
    }
    if not request.user.is_staff:
        return redirect('escritorio_instructores')
    return render(request, 'cursos/escritorio_directivo.html',context)



@login_required
def promedio_asistencias(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)
    
    # Obtener todos los estudiantes (regulares y PEN)
    estudiantes_regulares = curso.alumnos_inscriptos.all()
    estudiantes_pen = curso.alumnos_inscriptos_pen.all()
    
    # Obtener todas las clases del curso ordenadas por fecha
    clases_curso = Clase.objects.filter(curso=curso).order_by('fecha')
    
    # Calcular promedios para estudiantes regulares
    promedios = []
    for estudiante in estudiantes_regulares:
        total_clases = Asistencia.objects.filter(curso=curso, estudiante=estudiante).count()
        asistencias = Asistencia.objects.filter(curso=curso, estudiante=estudiante)
        presentes = sum([
            1 if a.estado == 'presente' else 0.5 if a.estado == 'media_falta' else 0
            for a in asistencias
        ])
        total_clases = asistencias.count()

        # Generar detalle de asistencia
        asistencias_map = {a.clase_id: a.estado for a in asistencias}
        detalle = []
        for idx, clase in enumerate(clases_curso, 1):
            estado = asistencias_map.get(clase.id)
            if estado == 'presente':
                code = 'P'
            elif estado == 'ausente':
                code = 'A'
            elif estado == 'media_falta':
                code = 'M'
            else:
                code = '00'
            detalle.append(f"{idx}/{code}")
        detalle_str = " ".join(detalle)

        promedio = (presentes / total_clases * 100) if total_clases > 0 else 0
        promedios.append({
            'nombre': f"{estudiante.first_name} {estudiante.last_name}",
            'dni': estudiante.dni_numero if hasattr(estudiante, 'dni_numero') else 'N/A',
            'promedio': round(promedio, 2),
            'detalle': detalle_str,
            'tipo': 'Regular'
        })

    # Calcular promedios para estudiantes PEN
    for estudiante_pen in estudiantes_pen:
        total_clases = Asistencia.objects.filter(curso=curso, estudiante_pen=estudiante_pen).count()
        asistencias_pen = Asistencia.objects.filter(curso=curso, estudiante_pen=estudiante_pen)
        presentes = sum([
            1 if a.estado == 'presente' else 0.5 if a.estado == 'media_falta' else 0
            for a in asistencias_pen
        ])
        total_clases = asistencias_pen.count()

        # Generar detalle de asistencia PEN
        asistencias_map_pen = {a.clase_id: a.estado for a in asistencias_pen}
        detalle_pen = []
        for idx, clase in enumerate(clases_curso, 1):
            estado = asistencias_map_pen.get(clase.id)
            if estado == 'presente':
                code = 'P'
            elif estado == 'ausente':
                code = 'A'
            elif estado == 'media_falta':
                code = 'M'
            else:
                code = '00'
            detalle_pen.append(f"{idx}/{code}")
        detalle_str_pen = " ".join(detalle_pen)

        promedio = (presentes / total_clases * 100) if total_clases > 0 else 0
        promedios.append({
            'nombre': estudiante_pen.nombre,
            'dni': estudiante_pen.dni,
            'promedio': round(promedio, 2),
            'detalle': detalle_str_pen,
            'tipo': 'PEN'
        })

    return JsonResponse({'promedios': promedios})



def obtener_dias_curso(request, curso_id):
    if request.method == 'GET':
        curso = get_object_or_404(Cursos, id=curso_id)
        dias_cursada = curso.dias_cursada()  # Usamos el método del modelo para obtener los días legibles
        return JsonResponse({'id': curso.id, 'nombre': curso.nombre, 'dias': dias_cursada})
    




@login_required
@require_GET
def exportar_asistencia_mes(request, curso_id, mes):
    from .models import Cursos, Clase, Asistencia

    curso = get_object_or_404(Cursos, id=curso_id)
    anio = datetime.now().year

    # Obtener clases del curso dentro del mes (días reales con clases)
    clases_en_mes = Clase.objects.filter(
        curso=curso,
        fecha__year=anio,
        fecha__month=mes
    )

    # Lista de fechas reales de clase en formato día/mes (ej: "5/7")
    dias_con_clases = [f"{clase.fecha.day}/{clase.fecha.month}" for clase in clases_en_mes]

    total_clases = clases_en_mes.count()

    estudiantes = []

    # Estudiantes regulares
    for estudiante in curso.alumnos_inscriptos.all():
        asistencias = Asistencia.objects.filter(
            curso=curso, estudiante=estudiante, fecha__year=anio, fecha__month=mes
        )
        asist_por_dia = {
            f"{a.fecha.day}/{a.fecha.month}": a.estado.capitalize() for a in asistencias
        }

        presentes = asistencias.filter(estado='presente').count()
        ausentes = asistencias.filter(estado='ausente').count()
        porcentaje = round((presentes / total_clases * 100) if total_clases > 0 else 0, 2)

        estudiantes.append({
            "nombre": f"{estudiante.first_name} {estudiante.last_name}",
            "dni": estudiante.inscripciones.filter(curso=curso).first().dni_numero if hasattr(estudiante, 'inscripciones') else '',
            "asistencias": {dia: asist_por_dia.get(dia, "") for dia in dias_con_clases},
            "total_clases": total_clases,
            "presentes": presentes,
            "ausentes": ausentes,
            "porcentaje": porcentaje,
        })

    # Estudiantes PEN
    for estudiante in curso.alumnos_inscriptos_pen.all():
        asistencias = Asistencia.objects.filter(
            curso=curso, estudiante_pen=estudiante, fecha__year=anio, fecha__month=mes
        )
        asist_por_dia = {
            f"{a.fecha.day}/{a.fecha.month}": a.estado.capitalize() for a in asistencias
        }

        presentes = asistencias.filter(estado='presente').count()
        ausentes = asistencias.filter(estado='ausente').count()
        porcentaje = round((presentes / total_clases * 100) if total_clases > 0 else 0, 2)

        estudiantes.append({
            "nombre": estudiante.nombre,
            "dni": estudiante.dni,
            "asistencias": {dia: asist_por_dia.get(dia, "") for dia in dias_con_clases},
            "total_clases": total_clases,
            "presentes": presentes,
            "ausentes": ausentes,
            "porcentaje": porcentaje,
        })

    return JsonResponse({
        "dias": dias_con_clases,
        "estudiantes": estudiantes
    })
@login_required
@require_POST
def actualizar_estado_inscripcion(request, inscripcion_id):
    """
    Vista para actualizar el estado de pago o certificado de una inscripción.
    """
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    curso = inscripcion.curso

    # Verificar permisos
    if not (request.user.is_staff or request.user == curso.instructor):
        return JsonResponse({'success': False, 'error': 'No tienes permiso para realizar esta acción.'}, status=403)

    campo = request.POST.get('campo')
    valor = request.POST.get('valor') == 'true'

    if campo in ['pago_contribucion', 'entrega_certificado']:
        setattr(inscripcion, campo, valor)
        inscripcion.save(update_fields=[campo])
        return JsonResponse({'success': True, 'message': f'Campo {campo} actualizado correctamente.'})
    else:
        return JsonResponse({'success': False, 'error': 'Campo no válido.'}, status=400)




@login_required
@require_POST
def procesar_ocr_dni(request):
    """
    Recibe la imagen vía AJAX, ejecuta OCR y devuelve el DNI encontrado
    para compararlo con el del usuario logueado.
    """
    imagen = request.FILES.get('imagen')
    
    if not imagen:
        return JsonResponse({'success': False, 'mensaje': 'No se recibió ninguna imagen.'})

    # SIMULACIÓN (OCR DESACTIVADO POR CONSUMO DE RECURSOS)
    # Devolvemos siempre éxito y coincidencias falsas para no bloquear, 
    # pero sin ejecutar el proceso pesado de 'extraer_dni_ocr'.
    
    dni_usuario = getattr(request.user.profile, 'dni', '')
    
    return JsonResponse({
        'success': True,
        'dni_detectado': dni_usuario, # Simulamos que detectamos el mismo DNI
        'dni_perfil': dni_usuario,
        'coincide': True,
        'mensaje': 'Validación por OCR desactivada.'
    })

@login_required
def lista_cursos_modulos(request):
    instructor = request.user
    cursos = Cursos.objects.filter(instructor=instructor).prefetch_related('modulos')
    modulos_sin_curso = Modulos.objects.filter(instructor=instructor, cursos_asociados__isnull=True)

    context = {
        'cursos': cursos,
        'modulos_sin_curso': modulos_sin_curso,
    }
    return render(request, 'cursos/lista_cursos_modulos.html', context)

@login_required
def mapa_conceptual_directivo(request):
    from django.contrib.auth.models import User
    from django.db.models import Count, Q
    
    # Obtener instructores con actividad
    # Obtener instructores con actividad
    instructores = User.objects.filter(
        profile__rol='instructor').annotate(
        total_cursos=Count('cursos_creados'), 
        total_modulos=Count('modulos_creados')
    ).filter(Q(total_cursos__gt=0) | Q(total_modulos__gt=0)).distinct()

    context = {
        'instructores': instructores,
    }
    return render(request, 'cursos/mapa_conceptual_directivo.html', context)


@login_required
def obtener_modulos_sin_curso_json(request):
    if not request.user.is_staff:
         return JsonResponse({'error': 'No autorizado'}, status=403)
    
    instructor_id = request.GET.get('instructor_id')
    
    query = Modulos.objects.filter(cursos_asociados__isnull=True)
    
    if instructor_id:
        query = query.filter(instructor_id=instructor_id)
        
    modulos = query.select_related('instructor')
    
    data = []
    for m in modulos:
        # Manejo seguro de días (puede ser None o lista)
        dias = m.dias
        if not dias:
            dias = []
            
        data.append({
            'id': m.id,
            'nombre': m.nombre,
            'descripcion': m.descripcion,
            'fecha_inicio_modulo': m.fecha_inicio_modulo.strftime("%Y-%m-%d") if m.fecha_inicio_modulo else None,
            'fecha_fin_modulo': m.fecha_fin_modulo.strftime("%Y-%m-%d") if m.fecha_fin_modulo else None,
            'dias': dias,
            'instructor_id': m.instructor.id,
            'instructor_nombre': f"{m.instructor.first_name} {m.instructor.last_name}"
        })
    
    return JsonResponse(data, safe=False)