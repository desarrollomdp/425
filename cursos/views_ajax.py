
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from cuentas.utils import extraer_dni_ocr
from django.core.files.storage import default_storage
import os

@require_POST
def extraer_dni_ajax(request):



    if 'imagen' not in request.FILES:
        return JsonResponse({'error': 'No se recibió ninguna imagen'}, status=400)
    
    imagen = request.FILES['imagen']
    
    try:
        # Extraer DNIs detectados
        dnis_detectados = extraer_dni_ocr(imagen)
        
        if dnis_detectados is None:
            return JsonResponse({
                'error': 'Error en el sistema OCR. Por favor, intente más tarde.',
                'dni': None
            })
        
        if dnis_detectados and len(dnis_detectados) > 0:
            # Tomar el primer DNI detectado (generalmente el más confiable)
            dni_principal = dnis_detectados[0]
            return JsonResponse({
                'success': True,
                'dni': dni_principal,
                'todos_dnis': dnis_detectados
            })
        else:
            return JsonResponse({
                'success': False,
                'dni': None,
                'error': 'No se detectó ningún número de DNI en la imagen'
            })
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error al procesar la imagen: {str(e)}',
            'dni': None
        }, status=500)
