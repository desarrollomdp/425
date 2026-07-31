from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Mensaje_socket
from cuentas.models import Profile # Importamos el perfil para filtrar por rol
from django.db import models
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required
def sala_chat(request, usuario_id):
    receptor = get_object_or_404(User, id=usuario_id)
    
    # Marcar como leídos los mensajes que recibí de este usuario
    Mensaje_socket.objects.filter(emisor=receptor, receptor=request.user, leido=False).update(leido=True)

    # Cargamos los últimos 50 mensajes para tener historial al entrar
    mensajes = Mensaje_socket.objects.filter(
        (models.Q(emisor=request.user) & models.Q(receptor=receptor)) |
        (models.Q(emisor=receptor) & models.Q(receptor=request.user))
    ).order_by('fecha')[:50]

    template_name = 'mensajes/chat.html'
    if request.GET.get('embed'):
        template_name = 'mensajes/chat_embed.html'

    return render(request, template_name, {
        'receptor': receptor,
        'mensajes': mensajes,
    })

@login_required
def sala_general(request):
    # Buscamos usuarios cuyo rol sea instructor o directivo
    # Excluimos al usuario actual para que no se vea a sí mismo en la lista
    personal_itinerante = User.objects.filter(
        profile__rol__in=['instructor', 'directivo']
    ).select_related('profile').exclude(id=request.user.id)

    return render(request, 'mensajes/sala_general.html', {
        'personal': personal_itinerante,
        'mensajes': Mensaje_socket.objects.all().order_by('fecha')
    })

@csrf_exempt
@login_required
def subir_archivo_chat(request):
    if request.method == 'POST' and request.FILES.get('archivo'):
        try:
            receptor_id = request.POST.get('receptor_id')
            archivo = request.FILES['archivo']
            
            mensaje = Mensaje_socket.objects.create(
                emisor=request.user,
                receptor_id=receptor_id,
                archivo=archivo
            )
            
            # --- PRINTS DE DEPURACIÓN ---
            print(f"DEBUG: Archivo recibido: {archivo.name}")
            print(f"DEBUG: URL generada: {mensaje.archivo.url}")
            print(f"DEBUG: ¿Es imagen?: {mensaje.es_imagen}")
            # ----------------------------
            
            return JsonResponse({
                'success': True,
                'url': mensaje.archivo.url,
                'es_imagen': mensaje.es_imagen,
                'mensaje_id': mensaje.id
            })
        except Exception as e:
            print(f"ERROR EN SUBIDA: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Petición inválida'}, status=400)

@login_required
def eliminar_mensaje(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje_socket, id=mensaje_id, emisor=request.user)
    # Eliminar el archivo físico del disco del VPS
    if mensaje.archivo:
        if os.path.isfile(mensaje.archivo.path):
            os.remove(mensaje.archivo.path)
    mensaje.delete()
    return JsonResponse({'success': True})

@login_required
def obtener_resumen_chats(request):
    user = request.user
    # Obtenemos todos los mensajes donde el usuario es emisor o receptor
    mensajes_asociados = Mensaje_socket.objects.filter(
        models.Q(emisor=user) | models.Q(receptor=user)
    ).order_by('-fecha')

    conversaciones_dict = {}
    total_unread = Mensaje_socket.objects.filter(receptor=user, leido=False).count()

    for m in mensajes_asociados:
        # El "otro" usuario es el que no soy yo
        otro_usuario = m.receptor if m.emisor == user else m.emisor
        
        if otro_usuario.id not in conversaciones_dict:
            conversaciones_dict[otro_usuario.id] = {
                'usuario_id': otro_usuario.id,
                'nombre': f"{otro_usuario.first_name} {otro_usuario.last_name}" if otro_usuario.first_name else otro_usuario.username,
                'avatar': otro_usuario.profile.avatar.url if hasattr(otro_usuario, 'profile') and otro_usuario.profile.avatar else None,
                'ultima_fecha': m.fecha.isoformat(),
                'ultimo_mensaje': m.contenido[:50] + '...' if m.contenido and len(m.contenido) > 50 else (m.contenido or "Archivo adjunto"),
                'unread_count': Mensaje_socket.objects.filter(emisor=otro_usuario, receptor=user, leido=False).count()
            }
            
    return JsonResponse({
        'total_unread': total_unread,
        'conversations': list(conversaciones_dict.values())
    })