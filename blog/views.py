from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import PostForm,ComentarioForm
from .models import Post


def es_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(es_admin)
def crear_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.autor = request.user
            post.save()
            return redirect('muro')  # Cambiá esto al nombre real de tu vista del muro
    else:
        form = PostForm()
    return render(request, 'blog/crear_post.html', {'form': form})





@login_required
def muro(request):
    publicaciones = Post.objects.all().order_by('-fecha_publicacion')
    return render(request, 'blog/muro.html', {'publicaciones': publicaciones})





@login_required
def muro(request):
    publicaciones = Post.objects.all().order_by('-fecha_publicacion')

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        post_id = request.POST.get('post_id')
        if form.is_valid() and post_id:
            comentario = form.save(commit=False)
            comentario.autor = request.user
            comentario.post_id = post_id
            comentario.save()
            return redirect('muro')  # o donde estés renderizando
    else:
        form = ComentarioForm()

    return render(request, 'blog/muro.html', {
        'publicaciones': publicaciones,
        'form': form
    })


@login_required
def editar_post(request, post_id):
    post = Post.objects.get(id=post_id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('muro')
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/editar_post.html', {'form': form, 'post': post})