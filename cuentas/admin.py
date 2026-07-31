# admin.py
from django.contrib import admin
from .models import Profile, Contacto
from django.core.mail import send_mail

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'rol')  # Agregamos 'email' a la lista
    list_filter = ('rol',)  # Filtro por rol
    search_fields = ('user__username', 'user__email')  # Agregamos búsqueda por email

    def email(self, obj):
        return obj.user.email  # Accedemos al email del usuario

    email.admin_order_field = 'user__email'  # Permite ordenar por email en el admin
    email.short_description = 'Email'  # Nombre más amigable en el admin


@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'fecha', 'respuesta')
    search_fields = ('nombre', 'email')
    fields = ('nombre', 'email', 'mensaje', 'respuesta', 'fecha')
    readonly_fields = ('nombre', 'email', 'mensaje', 'fecha')

    def save_model(self, request, obj, form, change):
        if 'respuesta' in form.changed_data:
            send_mail(
                'Respuesta a tu mensaje de contacto',
                obj.respuesta,
                'tu_email@examp7le.com',  # Cambia esto por el email desde el cual enviarás la respuesta
                [obj.email],
                fail_silently=False,
            )
        super().save_model(request, obj, form, change)

admin.site.register(Profile, ProfileAdmin)
