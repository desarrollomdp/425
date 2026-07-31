from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email
from django.contrib.auth import get_user_model

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Si el usuario ya está autenticado, no hacer nada
        if request.user.is_authenticated:
            return

        # Buscar usuario existente por email
        email = user_email(sociallogin.user)
        if email:
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                # Asociar la cuenta social con el usuario existente
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass  # No existe, se creará uno nuevo normalmente
