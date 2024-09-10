from django.urls import path
from .views import estadisticas_view

urlpatterns = [
    path('estadisticas/', estadisticas_view, name='estadisticas'),
]
