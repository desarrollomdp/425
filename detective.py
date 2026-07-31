# detective.py
import sys
try:
    import youtube_transcript_api
    from youtube_transcript_api import YouTubeTranscriptApi
    
    print("\n--- INFORME DEL DETECTIVE ---")
    print(f"1. Archivo cargado desde: {youtube_transcript_api.__file__}")
    print(f"2. ¿Tiene get_transcript?: {'get_transcript' in dir(YouTubeTranscriptApi)}")
    print("-----------------------------\n")
    
    if "site-packages" not in youtube_transcript_api.__file__:
        print("!!! ALERTA ROJA: Estás cargando un archivo local tuyo, NO la librería instalada.")
        print("-> BORRA O RENOMBRA EL ARCHIVO QUE MUESTRA EN EL PUNTO 1")
    else:
        print("La librería parece ser la correcta. El problema es la versión.")

except Exception as e:
    print(f"Error importando: {e}")