from django.urls import path
from .views import inscripcion_view, gracias_view, inicio_views
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path('votacion/', inscripcion_view, name='votacion'),
    path('gracias/', gracias_view, name='gracias'),
    path('', inicio_views, name='inicio'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
