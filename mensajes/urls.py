from django.urls import path
from . import views

urlpatterns = [
    path('general/', views.sala_general, name='sala_general'),
    path('chat/<int:usuario_id>/', views.sala_chat, name='sala_chat'),
    path('subir-archivo/', views.subir_archivo_chat, name='subir_archivo_chat'),
    path('eliminar-mensaje/<int:mensaje_id>/', views.eliminar_mensaje, name='eliminar_mensaje'),
    path('resumen/', views.obtener_resumen_chats, name='resumen_chats'),
    
]