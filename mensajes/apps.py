from django.apps import AppConfig


class MensajesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mensajes'
    
    def ready(self):
        # Importar signals para registrarlos
        import mensajes.signals
