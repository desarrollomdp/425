from django.urls import path
from . import views

urlpatterns = [
    path('crear/', views.crear_post, name='crear_post'),
    path('', views.muro, name='muro'),
    path('editar/<int:post_id>/', views.editar_post, name='editar_post'),

]
