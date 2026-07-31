from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta, datetime

from .models import Anuncio, ImpresionAnuncio, ClickAnuncio
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt


def _get_client_ip(request):
    # Soporta X-Forwarded-For si existe (proxy), si no usa REMOTE_ADDR
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@csrf_exempt
def registro_impresion(request, anuncio_id):
    """Recibe POST cuando un usuario ve/abre el anuncio. No falla si viene anónimo."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        anuncio = Anuncio.objects.get(pk=anuncio_id)
    except Anuncio.DoesNotExist:
        return JsonResponse({'error': 'anuncio_not_found'}, status=404)

    # Si hay usuario autenticado, crear registro físico e incrementar caché
    if request.user.is_authenticated:
        ImpresionAnuncio.objects.create(
            anuncio=anuncio,
            usuario=request.user,
            ip=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        try:
            cache_key = f'anuncio_visto_{request.user.id}_{anuncio.id}'
            contador = cache.get(cache_key, 0)
            nuevo = contador + 1
            cache.set(cache_key, nuevo, timeout=2592000)
            print(f"Registro impresion: user={request.user} id={request.user.id} anuncio={anuncio.id} vistas={nuevo}")
        except Exception:
            pass
    else:
        # Si es anónimo, incrementamos la vista usando la sesión
        try:
            session_key = f'anuncio_visto_anon_{anuncio.id}'
            contador = request.session.get(session_key, 0)
            nuevo = contador + 1
            request.session[session_key] = nuevo
            print(f"Registro impresion anonimo: anuncio={anuncio.id} vistas={nuevo}")
        except Exception:
            pass

    # Responder ok aun si no se creó (para no romper el frontend)
    return JsonResponse({'ok': True})


@csrf_exempt
def registro_click(request, anuncio_id):
    """Recibe POST cuando el usuario hace click en la imagen/CTA del anuncio."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        anuncio = Anuncio.objects.get(pk=anuncio_id)
    except Anuncio.DoesNotExist:
        return JsonResponse({'error': 'anuncio_not_found'}, status=404)

    if request.user.is_authenticated:
        ClickAnuncio.objects.create(
            anuncio=anuncio,
            usuario=request.user,
            ip=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    return JsonResponse({'ok': True})

def _parse_date(dstr):
    try:
        return datetime.fromisoformat(dstr)
    except Exception:
        return None


@login_required
def dashboard_anuncios(request):
    # Rango por defecto: últimos 7 días
    hasta = timezone.now()
    desde = hasta - timedelta(days=7)

    d = request.GET.get('desde')
    h = request.GET.get('hasta')
    if d:
        ddt = _parse_date(d)
        if ddt:
            desde = timezone.make_aware(ddt) if timezone.is_naive(ddt) else ddt
    if h:
        hdt = _parse_date(h)
        if hdt:
            hasta = timezone.make_aware(hdt) if timezone.is_naive(hdt) else hdt
        if h and len(h) == 10:
            hasta = hasta.replace(hour=23, minute=59, second=59)

    anuncios = Anuncio.objects.all().order_by('-id')

    filas = []
    for a in anuncios:
        imp_qs = ImpresionAnuncio.objects.filter(anuncio=a, timestamp__range=(desde, hasta))
        clk_qs = ClickAnuncio.objects.filter(anuncio=a, timestamp__range=(desde, hasta))

        IMP  = imp_qs.count()
        UV   = imp_qs.values('usuario').distinct().count()
        CLK  = clk_qs.count()
        UCLK = clk_qs.values('usuario').distinct().count()

        filas.append({
            "anuncio": a,
            "IMP": IMP,
            "UV": UV,
            "AVG": (IMP / UV) if UV else 0,
            "CLK": CLK,
            "UCLK": UCLK,
            "CTR_IMP": (CLK / IMP) if IMP else 0,
            "CTR_UV": (UCLK / UV) if UV else 0,
        })

    ctx = {"desde": desde, "hasta": hasta, "filas": filas}
    return render(request, "anuncios/dashboard_list.html", ctx)

# =================================================
# CRUD ANUNCIOS (Directivos)
# =================================================
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import AnuncioForm

class DirectivoRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        # Ajustar según la lógica de "Directivo" (ej. is_staff o grupo especifico)
        return self.request.user.is_authenticated and self.request.user.is_staff

class AnuncioListView(LoginRequiredMixin, DirectivoRequiredMixin, ListView):
    model = Anuncio
    template_name = 'anuncios/lista_anuncios.html'
    context_object_name = 'anuncios'
    ordering = ['-fecha_inicio']

class AnuncioCreateView(LoginRequiredMixin, DirectivoRequiredMixin, CreateView):
    model = Anuncio
    form_class = AnuncioForm
    template_name = 'anuncios/form_anuncio.html'
    success_url = reverse_lazy('anuncios:anuncios_list')

    def form_valid(self, form):
        # Podríamos asignar algo automático si hiciera falta
        return super().form_valid(form)

class AnuncioUpdateView(LoginRequiredMixin, DirectivoRequiredMixin, UpdateView):
    model = Anuncio
    form_class = AnuncioForm
    template_name = 'anuncios/form_anuncio.html'
    success_url = reverse_lazy('anuncios:anuncios_list')

class AnuncioDeleteView(LoginRequiredMixin, DirectivoRequiredMixin, DeleteView):
    model = Anuncio
    template_name = 'anuncios/confirmar_borrar.html'
    success_url = reverse_lazy('anuncios:anuncios_list')