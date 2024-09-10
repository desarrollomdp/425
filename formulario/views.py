from django.shortcuts import render, redirect
from .forms import InscripcionForm
from cursos.models import Categoria, Curso

def inscripcion_view(request):
    # Agrupamos los cursos por categoría
    categorias = Categoria.objects.all()
    cursos = Curso.objects.all()

    if request.method == 'POST':
        form = InscripcionForm(request.POST)
        
        if form.is_valid():
            # Verifica que solo se seleccionen 2 cursos
            if form.cleaned_data['cursos'].count() > 2:
                form.add_error('cursos', 'Puedes seleccionar solo hasta 2 cursos.')
            else:
                form.save()
                print("Formulario enviado y guardado.")  # Este mensaje se verá en la consola
                return redirect('gracias')
        else:
            print("Errores en el formulario:", form.errors)  # Imprimir errores si el formulario no es válido
    else:
        form = InscripcionForm()  # Si no es un POST, inicializa un nuevo formulario

    context = {
        'form': form,
        'categorias': categorias,
        'cursos': cursos,
    }

    return render(request, 'formulario/inscripcion.html', context)

def gracias_view(request):
    return render(request, 'formulario/gracias.html')

def inicio_views(request):
    return render(request, 'formulario/index.html')
