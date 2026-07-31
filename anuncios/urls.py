from django.urls import path
from . import views

app_name = 'anuncios'

urlpatterns = [
    path('', views.dashboard_anuncios, name='anuncios_dashboard'),
    
    # CRUD
    path('lista/', views.AnuncioListView.as_view(), name='anuncios_list'),
    path('crear/', views.AnuncioCreateView.as_view(), name='anuncios_create'),
    path('editar/<int:pk>/', views.AnuncioUpdateView.as_view(), name='anuncios_update'),
    path('eliminar/<int:pk>/', views.AnuncioDeleteView.as_view(), name='anuncios_delete'),

    # Endpoints para tracking (impresiones / clicks)
    path('impresion/<int:anuncio_id>/', views.registro_impresion, name='anuncio_impresion'),
    path('click/<int:anuncio_id>/', views.registro_click, name='anuncio_click'),
]