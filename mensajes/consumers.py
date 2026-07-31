import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
# No es necesario importar Mensaje_socket aquí arriba si lo haces dentro del método asíncrono

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.receptor_id = self.scope['url_route']['kwargs']['usuario_id']
        self.user = self.scope['user'] # Guardamos el usuario para fácil acceso
        self.emisor_id = self.user.id
        
        # 1. Grupo de la Sala (Para el chat actual)
        ids = sorted([int(self.emisor_id), int(self.receptor_id)])
        self.room_group_name = f'chat_{ids[0]}_{ids[1]}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # 2. Grupo Personal (Para recibir notificaciones de otros chats)
        self.user_group_name = f'user_{self.emisor_id}'
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Salir de ambos grupos al desconectar
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        mensaje_texto = data['message']
        file_url = data.get('file_url', None)
        es_imagen = data.get('es_imagen', False)

        # Guardar en la DB
        fecha_formateada = await self.guardar_mensaje(mensaje_texto, file_url, es_imagen)

        # A. Enviar el mensaje a la sala de chat actual
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': mensaje_texto,
                'sender_id': self.emisor_id,
                'timestamp': fecha_formateada
            }
        )

        # B. Enviar NOTIFICACIÓN al grupo personal del RECEPTOR
        # Usamos self.receptor_id que definimos en connect
        await self.channel_layer.group_send(
            f"user_{self.receptor_id}",
            {
                "type": "chat_notification",
                "mensaje": mensaje_texto,
                "emisor_nombre": f"{self.user.first_name} {self.user.last_name}",
                "emisor_id": self.user.id
            }
        )

    # Handler para mensajes normales de chat
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))

    # Handler para las NOTIFICACIONES (Paso C del lado del servidor)
    async def chat_notification(self, event):
        # Este método se dispara cuando alguien envía a f"user_{self.emisor_id}"
        # Solo lo enviamos si el emisor no soy yo mismo
        if event['emisor_id'] != self.emisor_id:
            await self.send(text_data=json.dumps({
                'type': 'chat_notification',
                'mensaje': event['mensaje'],
                'emisor_nombre': event['emisor_nombre'],
                'emisor_id': event['emisor_id']
            }))

    @database_sync_to_async
    def guardar_mensaje(self, contenido, file_url, es_imagen):
        from django.contrib.auth.models import User
        from django.utils import timezone
        from .models import Mensaje_socket
        receptor = User.objects.get(id=self.receptor_id)
        mensaje = Mensaje_socket.objects.create(
            emisor=self.user,
            receptor=receptor,
            contenido=contenido,
            archivo=file_url,
            es_imagen=es_imagen
        )
        return timezone.localtime(mensaje.fecha).strftime("%d/%m/%Y %H:%M")




# cuentas/consumers.py

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.user_id = self.scope["user"].id
            self.group_name = f"user_{self.user_id}"

            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_notification(self, event):
        # Este método envía el paquete al JavaScript
        await self.send(text_data=json.dumps(event))