from django import forms
from pydantic import ValidationError
from .models import Contacto
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Profile
class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ['nombre', 'email', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ingresa tu nombre'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ingresa tu email'
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Escribe tu mensaje aquí...',
                'rows': 5
            }),

        }


        
class MensajeForm(forms.Form):
    contenido = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Escribe tu mensaje...',
            'style': 'resize:none;'
        })
    )





# === ESTE ES EL FORMULARIO QUE MODIFICAMOS ===
# cuentas/formularios.py

class UserProfileForm(forms.ModelForm):
    # Campos de User
    first_name = forms.CharField(label="Nombre", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellido", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    # Campos de Profile
    avatar = forms.ImageField(label="Foto de Perfil", required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    dni = forms.CharField(label="DNI", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(label="Teléfono", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # NUEVO CAMPO: Fecha de Nacimiento
    fecha_nacimiento = forms.DateField(
        label="Fecha de Nacimiento", 
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Precargar datos del perfil en el formulario
        if self.instance.pk and hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['dni'].initial = profile.dni
            self.fields['telefono'].initial = profile.telefono
            self.fields['fecha_nacimiento'].initial = profile.fecha_nacimiento

    def save(self, commit=True):
        user = super().save(commit=commit)
        # Guardar manualmente los datos en el perfil
        if hasattr(user, 'profile'):
            profile = user.profile
            if self.cleaned_data.get('avatar'):
                profile.avatar = self.cleaned_data['avatar']
            
            profile.dni = self.cleaned_data.get('dni')
            profile.telefono = self.cleaned_data.get('telefono')
            profile.fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
            
            profile.save()
        return user



class FormularioCambioPassword(forms.Form):
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 or p2:
            if p1 != p2:
                raise ValidationError("Las contraseñas no coinciden.")
            try:
                validate_password(p1)
            except ValidationError as e:
                self.add_error('password1', e)
    nueva_contraseña = forms.CharField(
        label="Nueva contraseña", 
        widget=forms.PasswordInput, 
        required=False
    )
    repetir_contraseña = forms.CharField(
        label="Repetir contraseña", 
        widget=forms.PasswordInput, 
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        datos = super().clean()
        nueva = datos.get("nueva_contraseña")
        repetir = datos.get("repetir_contraseña")

        if nueva or repetir:
            if nueva != repetir:
                raise forms.ValidationError("Las contraseñas no coinciden.")
            if len(nueva) < 6:
                raise forms.ValidationError("La contraseña debe tener al menos 6 caracteres.")
            



class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Usuario o Email",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )





class RegistroManualForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Debe tener al menos 6 caracteres."
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    rol = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        label='Rol',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        validate_password(p1)

        return cleaned_data
