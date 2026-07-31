from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from cursos.views import escritorio_directivo
# Importamos las vistas de la app cursos


urlpatterns = [
    path('', views.index, name='inicio'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Ruta para el perfil de usuario
    path('profile/', views.user_profile, name='user_profile'),
    # Rutas de la app cursos
    path ('contacto/',views.contacto_view, name='contacto'),
    path ('escritorio_directivo/', escritorio_directivo, name='escritorio_directivo'),
    path('evaluacion/', views.evaluacion, name='evaluacion'),
    path('evaluacion/resultados/', views.evaluacion_resultado, name='evaluacion_resultado'),
    path('gestionar-sliders/', views.gestionar_sliders, name='gestionar_sliders'),
    path('detalles_curso/<int:curso_id>/', views.detalles_curso, name='detalles_curso'),
    path('inicioporcontraseña/', views.inicio_por_contraseña, name='inicioporcontraseña'),
    path('todos_los_usuarios/', views.todos_los_usuarios, name='todos_los_usuarios'),


]


