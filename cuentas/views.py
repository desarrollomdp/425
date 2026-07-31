from django.shortcuts import render, redirect,get_object_or_404
from .formularios import ContactoForm, FormularioCambioPassword,UserProfileForm,RegistroManualForm,MensajeForm, LoginForm
from django.contrib import messages
from .models import Profile, Contacto
from cursos.models import Cursos, Modulos, Nota
from django.core.mail import send_mail
from .models import EvaluacionCelulares
# from allauth.account.forms import LoginForm
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test,login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import authenticate, login
from functools import wraps
from mensajes.models import Mensaje_socket
from cursos.models import Inscripcion
from django.http import JsonResponse
import os
from .utils import comprimir_imagen
def listar_todos_usuarios():
    print("\nListado de todos los usuarios en la base de datos:")
    print("----------------------------------------------")
    usuarios = User.objects.all()
    for usuario in usuarios:
        try:
            perfil = Profile.objects.get(user=usuario)
            rol = perfil.rol
        except Profile.DoesNotExist:
            rol = "Sin perfil"
        
        print(f"ID: {usuario.id}")
        print(f"Username: {usuario.username}")
        print(f"Email: {usuario.email}")
        print(f"Rol: {rol}")
        print("----------------------------------------------")

def buscar_usuario_por_email(email="desarrollomdp09@gmail.com"):
    # Primero mostrar todos los usuarios
    listar_todos_usuarios()
    
    try:
        # Buscar usuario por email
        usuario = User.objects.get(email=email)
        print(f"\nUsuario encontrado por email {email}:")
        print(f"ID: {usuario.id}")
        print(f"Username: {usuario.username}")
        print(f"Email: {usuario.email}")
        
        try:
            perfil = Profile.objects.get(user=usuario)
            print(f"Rol: {perfil.rol}")
        except Profile.DoesNotExist:
            print("El usuario no tiene un perfil asociado")
            
        return usuario
    except User.DoesNotExist:
        print(f"\nNo se encontró ningún usuario con el email {email}")
        return None

def custom_login_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, settings.MESSAGE_LOGIN_REQUIRED)
            return redirect(settings.LOGIN_URL)
        return function(request, *args, **kwargs)
    return wrap

@custom_login_required
def user_profile(request):
    user = request.user
    profile = Profile.objects.get(user=user)
    cursos = Cursos.objects.filter(instructor=request.user)
    notas = Nota.objects.filter(estudiante=user)
    modulos = Modulos.objects.filter(instructor=request.user)
    cursos_aprobados = [curso for curso in cursos if curso.aprobado]
    conversaciones = Contacto.objects.filter(email=user.email)
    inscripciones = Inscripcion.objects.filter(usuario=user) # ✅ Correcto
    # mensajes = Mensaje_socket.objects.all().order_by('fecha') # Reemplazado por lógica optimizada abajo
    if request.method == 'POST':
        form = UserProfileForm(request.POST,request.FILES, instance=user)
        form_pw = FormularioCambioPassword(request.POST)

        if form.is_valid() and form_pw.is_valid():
            form.save()
            nueva = form_pw.cleaned_data.get('nueva_contraseña')
            if nueva:
                user.set_password(nueva)
                user.save()
                update_session_auth_hash(request, user)
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect('user_profile')
        else:
            messages.error(request, 'Por favor corrige los errores')
    else:
        form = UserProfileForm(instance=user)
        form_pw = FormularioCambioPassword()
    # Lógica para la Bandeja de Entrada - Estilo WhatsApp
    # Obtenemos todos los mensajes donde el usuario participa
    my_messages = Mensaje_socket.objects.filter(
        Q(emisor=user) | Q(receptor=user)
    ).select_related('emisor', 'receptor').order_by('-fecha')

    recent_chats = []
    seen_users = set()

    for msg in my_messages:
        partner = msg.receptor if msg.emisor == user else msg.emisor
        if partner.id not in seen_users:
            seen_users.add(partner.id)
            recent_chats.append({
                'user': partner,
                'last_message': msg
            })
            if len(recent_chats) >= 20: # Límite de 20 chats
                break

    return render(request, 'cuentas/user_profile.html', {
        'form': form,
        'form_pw': form_pw,
        'cursos': cursos,
        'modulos': modulos,
        'profile': profile,
        'notas': notas,
        'cursos_aprobados': cursos_aprobados,
        'conversaciones': conversaciones, # Historial de formulario de contacto
        'es_staff': user.is_staff,
        'recent_chats': recent_chats,
        'inscripciones': inscripciones,
    })

def index(request):
    form = LoginForm()
    cursos_abiertos = Cursos.objects.filter(
        inscripcion_abierta=True,
    )
    return render(request, 'cuentas/inicio.html', {
        'form': form,
        'cursos_abiertos': cursos_abiertos
    })

def contacto_view(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            contacto = Contacto.objects.create(
                nombre=form.cleaned_data['nombre'],
                email=form.cleaned_data['email'],
                mensaje=form.cleaned_data['mensaje'],
                respuesta=form.cleaned_data.get('respuesta', '')  # Guardar la respuesta si está presente
            )
            if contacto.respuesta:
                send_mail(
                    'Respuesta a tu mensaje de contacto',
                    contacto.respuesta,
                    'tu_email@example.com',  # Cambia esto por el email desde el cual enviarás la respuesta
                    [contacto.email],
                    fail_silently=False,
                )
            messages.success(request, 'Tu mensaje ha sido enviado exitosamente.')
            return redirect('mensaje_enviado')
        else:
            messages.error(request, 'Por favor, corrige los errores.')
    else:
        form = ContactoForm()
    
    return render(request, 'cuentas/contacto.html', {'form': form})


def evaluacion(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        apellido = request.POST.get('apellido', '')
        dni = request.POST.get('dni', '')

        respuestas_objetivas = {f'q{i}': int(request.POST.get(f'q{i}', 0)) for i in range(1, 11)}
        respuestas_abiertas = {f'q{i}': request.POST.get(f'q{i}', '') for i in range(11, 17)}
        puntaje = sum(respuestas_objetivas.values())

        EvaluacionCelulares.objects.create(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            puntaje_objetivo=puntaje,
            respuestas_objetivas=respuestas_objetivas,
            respuestas_abiertas=respuestas_abiertas
        )

        return redirect('inicio')

    return render(request, 'cuentas/evaluacion.html')

def evaluacion_resultado(request):
    resultados = EvaluacionCelulares.objects.order_by('-fecha')[:10]  # últimos 10
    return render(request, 'cuentas/evaluacion_resultado.html', {'resultados': resultados})

@staff_member_required
def gestionar_sliders(request):
    sliders = [
        {'key': 'slider1_desktop', 'label': 'Slider 1 (Desktop)'},
        {'key': 'slider2_desktop', 'label': 'Slider 2 (Desktop)'},
        {'key': 'slider3_desktop', 'label': 'Slider 3 (Desktop)'},
        {'key': 'slider1_mobile', 'label': 'Slider 1 (Mobile)'},
        {'key': 'slider2_mobile', 'label': 'Slider 2 (Mobile)'},
        {'key': 'slider3_mobile', 'label': 'Slider 3 (Mobile)'},
    ]

    if request.method == 'POST':
        for slider in sliders:
            key = slider['key']
            archivo_nuevo = request.FILES.get(key)

            if archivo_nuevo:
                # Validar extensiones permitidas
                extension = archivo_nuevo.name.lower().split('.')[-1]
                if extension not in ['jpg', 'jpeg', 'png', 'webp']:
                    messages.error(request, f"'{key}' debe ser una imagen (jpg, jpeg, png, webp).")
                    continue

                # Definir dimensiones según el tipo de slider
                dimensiones = (1920, 1080) if 'desktop' in key else (1080, 1920)

                # Convertir a WebP usando la utilidad
                archivo_webp = comprimir_imagen(archivo_nuevo, f"{key}.webp", dimensiones=dimensiones)

                if archivo_webp:
                    ruta_estatica = os.path.join(settings.BASE_DIR, 'static', 'images')
                    ruta_archivo = os.path.join(ruta_estatica, f'{key}.webp')

                    # Eliminar archivos viejos (posibles .jpg o .png remanentes y el .webp actual)
                    for ext in ['.jpg', '.png', '.webp']:
                        vieja_ruta = os.path.join(ruta_estatica, f'{key}{ext}')
                        if os.path.exists(vieja_ruta):
                            os.remove(vieja_ruta)

                    # Guardar nueva imagen WebP
                    try:
                        with open(ruta_archivo, 'wb+') as destino:
                            for chunk in archivo_webp.chunks():
                                destino.write(chunk)
                        messages.success(request, f"Imagen '{slider['label']}' actualizada y convertida a WebP.")
                    except Exception as e:
                        messages.error(request, f"No se pudo guardar '{slider['label']}': {str(e)}")

        return redirect('gestionar_sliders')

    return render(request, 'cuentas/gestionar_sliders.html', {'sliders': sliders})


def es_staff(user):
    return user.is_staff


def detalles_curso(request, curso_id):
    curso = get_object_or_404(Cursos, id=curso_id)


    return render(request, 'cuentas/detalles_curso.html', {
        'curso': curso,

    })

def inicio_por_contraseña(request):
    print(f"\n--- Intento de login por contraseña ---")
    if request.method == "POST":
        print(f"POST data: {request.POST}")
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']
            print(f"Buscando usuario: {username_or_email}")

            # Primero buscamos si el usuario existe por username o email
            user_obj = User.objects.filter(Q(username=username_or_email) | Q(email=username_or_email)).first()

            if not user_obj:
                print("Resultado: La cuenta no existe.")
                form.add_error(None, "La cuenta no existe.")
            else:
                print(f"Usuario encontrado: {user_obj.username}. Intentando autenticar...")
                # El usuario existe, intentamos autenticar con su username real
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None:
                    print(f"Autenticación exitosa para: {user.username}")
                    login(request, user)
                    return redirect('inicio')
                else:
                    print("Resultado: Contraseña incorrecta.")
                    form.add_error(None, "La contraseña es incorrecta.")
        else:
            print(f"Errores de formulario: {form.errors}")
    else:
        form = LoginForm()
    return render(request, "cuentas/login.html", {"form": form})

def registrar_usuario_manual(request):
    if request.method == 'POST':
        # Modificar el POST data para usar el valor correcto de rol
        post_data = request.POST.copy()
        if post_data.get('rol') == 'estudiante':
            post_data['rol'] = 'alumno'
        
        form = RegistroManualForm(post_data)
        print("POST Data (modified):", post_data)  # Debug: ver los datos recibidos
        
        if form.is_valid():
            print("Form is valid")  # Debug: confirmar validación
            try:
                # Verificar si el usuario ya existe
                email = form.cleaned_data.get('email')
                username = form.cleaned_data.get('username')
                
                # Debug: Buscar usuarios existentes
                existing_email = User.objects.filter(email=email)
                existing_username = User.objects.filter(username=username)
                
                print("\nVerificación de usuario existente:")
                print(f"Buscando email: {email}")
                print(f"Buscando username: {username}")
                print(f"Usuarios con este email: {list(existing_email.values('id', 'username', 'email'))}")
                print(f"Usuarios con este username: {list(existing_username.values('id', 'username', 'email'))}")
                
                # Debug: Verificar perfiles existentes
                existing_profiles = Profile.objects.filter(
                    user__in=User.objects.filter(Q(email=email) | Q(username=username))
                )
                print(f"Perfiles existentes para este usuario: {list(existing_profiles.values())}")
                
                if existing_email.exists() or existing_username.exists():
                    if existing_email.exists():
                        messages.error(request, f'Ya existe un usuario con el email {email}')
                    if existing_username.exists():
                        messages.error(request, f'Ya existe un usuario con el nombre de usuario {username}')
                    return render(request, 'account/signup.html', {'form': form})

                from django.db import transaction
                with transaction.atomic():
                    # Verificar contraseñas
                    password1 = form.cleaned_data.get('password1')
                    password2 = form.cleaned_data.get('password2')
                    
                    if password1 != password2:
                        messages.error(request, 'Las contraseñas no coinciden')
                        return render(request, 'account/signup.html', {'form': form})
                    
                    # Crear usuario
                    user = form.save(commit=False)
                    print("User before save:", user.__dict__)  # Debug: ver objeto usuario
                    user.set_password(password1)
                    user.save()
                    
                    # Verificar si ya existe un perfil para este usuario
                    try:
                        profile = Profile.objects.get(user=user)
                        print("Perfil existente encontrado:", profile.__dict__)
                        profile.rol = 'alumno'
                        profile.save()
                    except Profile.DoesNotExist:
                        # Crear perfil con rol 'alumno' solo si no existe
                        profile = Profile.objects.create(user=user, rol='alumno')
                        print("Nuevo perfil creado:", profile.__dict__)  # Debug: ver perfil creado
                    
                    # Iniciar sesión
                    from django.contrib.auth import login
                    # Especificar backend explícitamente para evitar error de múltiples backends
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    
                    messages.success(request, 'Usuario registrado correctamente.')
                    return redirect('user_profile')
                    
            except Exception as e:
                print("Error:", str(e))  # Debug: ver error completo
                messages.error(request, f'Error al registrar usuario: {str(e)}')
                if 'user' in locals():
                    user.delete()
        else:
            print("Form errors:", form.errors)  # Debug: ver errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
        
        # Si llegamos aquí, hubo algún error
        return render(request, 'account/signup.html', {'form': form})
    
    # GET request
    form = RegistroManualForm()
    return render(request, 'account/signup.html', {'form': form})


from django.http import JsonResponse
from django.contrib.auth.models import User
@login_required
def todos_los_usuarios(request):
    # Optimización: select_related para evitar el problema N+1 en la RAM y CPU
    usuarios = User.objects.select_related('profile').all()
    
    data = []
    for usuario in usuarios:
        # Verificamos de forma segura si el usuario tiene un perfil asociado
        tiene_perfil = hasattr(usuario, 'profile')
        
        data.append({
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            
            # Corregido el typo "rofile" y agregado el campo DNI viajando por el perfil
            'rol': usuario.profile.rol if tiene_perfil else 'No asignado',
            'dni': usuario.profile.dni if tiene_perfil else 'Sin DNI',
        })
        
    return JsonResponse(data, safe=False)