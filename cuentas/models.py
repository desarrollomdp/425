# cuentas/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import comprimir_imagen

class Profile(models.Model):
    ROLE_CHOICES = [
        ('alumno', 'Alumno'),
        ('instructor', 'Instructor'),
        ('directivo', 'Directivo'),
        ('adminpen','adminpen')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rol = models.CharField(max_length=10, choices=ROLE_CHOICES, default='alumno')
    
    # Campo de Avatar
    avatar = models.ImageField(upload_to='avatares/', default='avatares/default.webp', blank=True, null=True)
    
    # Datos extra
    dni = models.CharField(max_length=20, blank=True, null=True, verbose_name="DNI")
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de Nacimiento")
    
    # Campo interno para versionar las fotos (v1, v2, v3...)
    avatar_version = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"

    def save(self, *args, **kwargs):
        # Si hay un avatar cargado...
        if self.avatar:
            try:
                # Verificamos si es una actualización (el perfil ya existe)
                if self.pk:
                    old_profile = Profile.objects.get(pk=self.pk)
                    
                    # Si la imagen cambió (es nueva)
                    if self.avatar != old_profile.avatar:
                        # 1. Borrar la imagen anterior (Compatible con R2 y Local)
                        if old_profile.avatar and "default.webp" not in old_profile.avatar.name:
                            # .delete(save=False) borra el archivo físico sin guardar el modelo de nuevo
                            old_profile.avatar.delete(save=False)
                        
                        # 2. Aumentar versión
                        self.avatar_version += 1
                        
                        # 3. Generar nuevo nombre: "usuario_juanperez_v5.webp"
                        nombre_limpio = f"usuario_{self.user.username}_v{self.avatar_version}.webp"
                        
                        # 4. Comprimir con el nuevo nombre
                        self.avatar = comprimir_imagen(self.avatar, nombre_limpio)
                
                else:
                    # Es creación nueva
                    self.avatar_version = 1
                    nombre_limpio = f"usuario_{self.user.username}_v1.webp"
                    self.avatar = comprimir_imagen(self.avatar, nombre_limpio)
            
            except Exception as e:
                print(f"⚠️ Error procesando avatar: {e}")
                # Importante: No detenemos el guardado si falla la imagen
        
        super(Profile, self).save(*args, **kwargs)


# === SEÑALES (Automatización) ===

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# === OTROS MODELOS ===
class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    respuesta = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.nombre} - {self.email}'

class EvaluacionCelulares(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50, default='')
    dni = models.CharField(max_length=15, default='')
    puntaje_objetivo = models.IntegerField()
    respuestas_objetivas = models.JSONField()
    respuestas_abiertas = models.JSONField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - DNI: {self.dni}"