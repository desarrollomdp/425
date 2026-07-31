from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # La URL tendrá el ID del usuario con el que queremos hablar
    re_path(r'ws/chat/(?P<usuario_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()), # 🔔 Nueva ruta
]