from django.shortcuts import render
from django.db.models import Count
from formulario.models import Inscripcion
import matplotlib.pyplot as plt
import io
import urllib, base64

def estadisticas_view(request):
    # Obtener los datos de inscripciones agrupados por curso
    datos = Inscripcion.objects.values('cursos__nombre', 'cursos__categoria').annotate(total=Count('id')).order_by('-total')

    # Nombres de los cursos y sus correspondientes cantidades
    cursos_categoria = {}
    for dato in datos:
        curso_nombre = dato['cursos__nombre']
        categoria_nombre = dato['cursos__categoria'] or 'Sin categoría'  # Asigna 'Sin categoría' si no hay categoría

        if categoria_nombre not in cursos_categoria:
            cursos_categoria[categoria_nombre] = []
        
        # Aquí puedes agregar el rango de edad, si es necesario
        rangos = Inscripcion.objects.filter(cursos__nombre=curso_nombre).values_list('edad', flat=True)
        rango_edad = f"{min(rangos)} - {max(rangos)}" if rangos else "N/A"

        cursos_categoria[categoria_nombre].append((curso_nombre, rango_edad))

    # Generar el gráfico
    plt.figure(figsize=(10, 5))
    plt.pie([dato['total'] for dato in datos], labels=[dato['cursos__nombre'] for dato in datos], autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie chart is drawn as a circle.
    
    # Convertir el gráfico en una imagen que se pueda incrustar en HTML
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)

    return render(request, 'estadisticas/estadisticas.html', {'data': uri, 'cursos': cursos_categoria})
