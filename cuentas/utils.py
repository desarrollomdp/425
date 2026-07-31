# cuentas/utils.py

import sys
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
import cv2
import numpy as np
import pytesseract
from django.utils.text import slugify
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re

import pytesseract
import os
import platform

# Detectar si estamos en Windows o Linux
if platform.system() == 'Windows':
    # Ruta local
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # En Linux (VPS), tesseract suele estar en el PATH global, 
    # por lo que no hace falta definirlo, o suele estar en /usr/bin/tesseract
    tesseract_cmd = '/usr/bin/tesseract'
    if os.path.exists(tesseract_cmd):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

# ... resto de tu función extraer_dni_ocr ...
# Configuración para Windows: SI Tesseract no está en el PATH, descomenta y ajusta la siguiente ruta:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def generar_ruta_inscripcion(instance, filename):
    """
    Genera la ruta: inscripciones/nombre-curso/username/tipo_archivo.webp
    """
    curso_nombre = slugify(instance.curso.nombre)
    usuario_nombre = slugify(instance.usuario.username)
    extension = "webp"
    
    # Determinamos qué campo se está guardando
    # Esto es una simplificación, en el modelo lo manejaremos mejor
    return f"inscripciones/{curso_nombre}/{usuario_nombre}/{filename}"

def verificar_nitidez(imagen_field):
    """
    Usa la Varianza de Laplacian para determinar si la imagen está enfocada.
    """
    try:
        # Convertir imagen de Django a formato OpenCV
        file_bytes = np.asarray(bytearray(imagen_field.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
        imagen_field.seek(0) # Resetear el puntero del archivo

        # Calcular variancia (Score de enfoque)
        score = cv2.Laplacian(img, cv2.CV_64F).var()
        
        print(f"[DEBUG-NITIDEZ] Score: {score}")
        
        # Un score menor a 100 suele ser borroso. 
        # Puedes ajustar este número según tus pruebas.
        return score > 80 
    except Exception as e:
        print(f"Error en validación de nitidez: {e}")
        return True # Por seguridad, si falla el motor, dejamos pasar

def extraer_dni_ocr(imagen_field):
    """
    Procesa la imagen para resaltar texto negro sobre fondo claro
    y busca patrones de DNI.
    """
    try:
        # 1. Abrir imagen
        img = Image.open(imagen_field)

        # 2. Convertir a Escala de Grises
        img = img.convert('L')

        # 3. Aumentar el contraste (ayuda a distinguir las letras del fondo)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0) # Duplicamos el contraste

        # 4. Binarización (Umbral): Convertir a Blanco y Negro puro
        # Todo píxel más claro que 140 se vuelve blanco (fondo), el resto negro (texto)
        # Esto elimina las "olitas" del fondo del DNI
        thresh = 140
        fn = lambda x : 255 if x > thresh else 0
        img = img.point(fn, mode='1')

        # (Opcional) Si quieres ver cómo quedó la imagen procesada en tu carpeta del proyecto:
        # img.save('debug_dni_procesado.png') 

        # 5. Ejecutar OCR
        # --psm 6: Asume un bloque de texto uniforme (funciona mejor para DNI)
        custom_config = r'--oem 3 --psm 6'
        texto_crudo = pytesseract.image_to_string(img, config=custom_config)

        print(f"\n[DEBUG-OCR] Texto detectado: {texto_crudo}")

        # 6. ESTRATEGIA DE BÚSQUEDA MEJORADA
        # El DNI en la foto es "37.381.044". Tesseract puede leerlo con puntos o espacios.
        
        # Paso A: Buscar formato con puntos (ej: 37.381.044)
        # Regex explica: (1 o 2 digitos) + punto + (3 digitos) + punto + (3 digitos)
        match_con_puntos = re.search(r'\b\d{1,2}\.\d{3}\.\d{3}\b', texto_crudo)
        
        if match_con_puntos:
            dni_limpio = match_con_puntos.group(0).replace('.', '')
            print(f"[DEBUG-OCR] DNI con puntos encontrado: {dni_limpio}")
            return [dni_limpio]

        # Paso B: Si falla, limpiamos todo lo que NO sea número y buscamos secuencia
        # Esto sirve si Tesseract leyó "37 381 044" o "37381044"
        texto_solo_numeros = re.sub(r'[^0-9]', '', texto_crudo) # Eliminar todo menos números
        
        # Buscamos en esa "sopa de números" secuencias de 7 u 8 cifras
        # Pero cuidado, el trámite (abajo) tiene 11 números. El DNI suele estar antes.
        numeros_potenciales = re.findall(r'\d{7,8}', texto_solo_numeros)

        # Filtramos números que parecen DNI (entre 5 millones y 100 millones)
        dnis_validos = []
        for num in numeros_potenciales:
            val = int(num)
            if 5_000_000 < val < 100_000_000:
                dnis_validos.append(num)
        
        print(f"[DEBUG-OCR] Candidatos encontrados: {dnis_validos}")
        
        if dnis_validos:
            # Retornamos el primero que suele ser el más relevante o el único
            return dnis_validos
            
        return None

    except Exception as e:
        print(f"🚨 [DEBUG-OCR] ERROR CRÍTICO: {e}")
        return None
    


def comprimir_imagen(campo_imagen, nombre_archivo, calidad=85, dimensiones=(800, 800)):
    """
    Recibe un archivo de imagen, lo redimensiona y lo convierte a WebP.
    Incluye logs de debug para monitorear el proceso en consola.
    """
    print(f"\n[IMG-DEBUG] --- Iniciando proceso para: {nombre_archivo} ---")

    if not campo_imagen:
        print("[IMG-DEBUG] ❌ No se recibió ningún archivo de imagen.")
        return None

    try:
        # 1. Abrir la imagen con Pillow
        imagen = Image.open(campo_imagen)
        print(f"[IMG-DEBUG] 1. Imagen abierta. Formato original: {imagen.format}, Tamaño: {imagen.size}")

        # 2. Convertir a RGB 
        # (Necesario porque WebP y JPG no soportan el modo 'P' o 'RGBA' directo a veces)
        if imagen.mode in ('RGBA', 'P', 'CMYK'):
            print(f"[IMG-DEBUG] 2. Modo {imagen.mode} detectado. Convirtiendo a RGB...")
            imagen = imagen.convert('RGB')
        else:
            print("[IMG-DEBUG] 2. Modo de color correcto (RGB), no se requiere conversión.")

        # 3. Redimensionar (Thumbnail)
        # Usamos las dimensiones pasadas como parámetro.
        imagen.thumbnail(dimensiones, Image.Resampling.LANCZOS)
        print(f"[IMG-DEBUG] 3. Redimensionado completado. Nuevas dimensiones: {imagen.size}")

        # 4. Guardar en memoria (Buffer)
        buffer_salida = BytesIO()
        imagen.save(buffer_salida, format='WebP', quality=calidad, optimize=True)
        buffer_salida.seek(0) # Volver al inicio del archivo en memoria
        print("[IMG-DEBUG] 4. Imagen guardada en buffer de memoria como WebP.")

        # 5. Calcular nuevo nombre y pesos
        nombre_limpio = nombre_archivo.split('.')[0]
        nuevo_nombre = f"{nombre_limpio}.webp"
        
        peso_original = campo_imagen.size if hasattr(campo_imagen, 'size') else 0
        peso_nuevo = sys.getsizeof(buffer_salida)

        print(f"[IMG-DEBUG] 5. Cambio de nombre: '{nombre_archivo}' -> '{nuevo_nombre}'")
        print(f"[IMG-DEBUG] 📊 ESTADÍSTICAS DE AHORRO:")
        print(f"   - Peso Original: {peso_original / 1024:.2f} KB")
        print(f"   - Peso Final:    {peso_nuevo / 1024:.2f} KB")

        # 6. Crear el objeto de archivo para Django
        archivo_final = InMemoryUploadedFile(
            buffer_salida,
            'ImageField',
            nuevo_nombre,
            'image/webp',
            peso_nuevo,
            None
        )
        print("[IMG-DEBUG] ✅ Proceso finalizado con éxito. Devolviendo archivo.")
        print("--------------------------------------------------\n")
        
        return archivo_final

    except Exception as e:
        print(f"[IMG-DEBUG] 🚨 ERROR CRÍTICO durante la compresión: {str(e)}")
        print("[IMG-DEBUG] ⚠️ Se devolverá la imagen original sin modificar para no perder datos.")
        return campo_imagen