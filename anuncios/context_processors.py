from .models import Anuncio
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def anuncio_activo(request):
    """
    Context processor que provee el anuncio vigente de mayor prioridad.
    Limita la visualización a máximo 3 veces por usuario usando cache/sesión.
    Excluye páginas críticas como login, perfil e inscripciones.
    """
    # 1. Excluir URLs de administración, autenticación, perfil e inscripción
    path = request.path
    urls_excluidas = [
        '/admin/',
        '/accounts/',
        '/inicioporcontraseña/',
        '/inicioporcontraseñainstructores/',
        '/inicioporcodigo/',
        '/profile/',
        '/cursos/inscribirse/',
        '/mensajes/',
        '/reportes/',
        '/logout/',
    ]
    if any(excluida in path for excluida in urls_excluidas):
        return {
            "anuncio_activo": None,
            "anuncio_tiene_link": False,
            "mostrar_anuncio": False
        }

    qs = Anuncio.objects.all()
    # Filtro de vigencia simple
    activos = [a for a in qs if a.esta_vigente]
    anuncio = activos[0] if activos else None
    
    # Lógica de cache para limitar visualizaciones (máximo 5 veces por anuncio)
    mostrar_anuncio = True
    if anuncio:
        if request.user.is_authenticated:
            cache_key = f'anuncio_visto_{request.user.id}_{anuncio.id}'
            contador_vistas = cache.get(cache_key, 0)
            mostrar_anuncio = contador_vistas < 5
        else:
            # Para usuarios anónimos (invitados), usamos la sesión del navegador
            session_key = f'anuncio_visto_anon_{anuncio.id}'
            contador_vistas = request.session.get(session_key, 0)
            mostrar_anuncio = contador_vistas < 5
        
    # Determinar si el anuncio tiene URL o WhatsApp (para elegir el template correcto)
    tiene_link = False
    if anuncio and mostrar_anuncio:
        tiene_link = bool(anuncio.url_destino or anuncio.whatsapp)
    
    return {
        "anuncio_activo": anuncio if mostrar_anuncio else None,
        "anuncio_tiene_link": tiene_link,
        "mostrar_anuncio": mostrar_anuncio
    }
