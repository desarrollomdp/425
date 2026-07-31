from django.db.models import Count
from .models import ImpresionAnuncio, ClickAnuncio

def kpis_anuncio(anuncio, desde, hasta):
    imp_qs = ImpresionAnuncio.objects.filter(anuncio=anuncio, timestamp__range=(desde, hasta))
    clk_qs = ClickAnuncio.objects.filter(anuncio=anuncio, timestamp__range=(desde, hasta))

    IMP = imp_qs.count()
    UV = imp_qs.values('usuario').distinct().count()
    CLK = clk_qs.count()
    UCLK = clk_qs.values('usuario').distinct().count()

    avg = (IMP / UV) if UV else 0
    ctr_imp = (CLK / IMP) if IMP else 0
    ctr_uv = (UCLK / UV) if UV else 0

    return {
        "IMP": IMP,
        "UV": UV,
        "AVG_VIEWS_PER_USER": avg,
        "CLK": CLK,
        "UCLK": UCLK,
        "CTR_IMP": ctr_imp,
        "CTR_UV": ctr_uv,
    }
