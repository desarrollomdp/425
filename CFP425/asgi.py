import os
import django
from django.core.asgi import get_asgi_application

# 1. Configurar entorno (¡OJO: Mayúsculas!)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CFP425.settings')

# 2. Inicializar Django (Vital para que carguen los modelos antes que el chat)
django.setup()

# 3. Importar canales DESPUÉS del setup
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import mensajes.routing

application = ProtocolTypeRouter({
    # Django maneja las peticiones HTTP normales
    "http": get_asgi_application(),
    
    # Channels maneja los WebSockets
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                mensajes.routing.websocket_urlpatterns
            )
        )
    ),
})