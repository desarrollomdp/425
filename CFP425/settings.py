"""
Django settings for CFP425 project.
Refactorizado para Producción/Seguridad
"""

from pathlib import Path
import os
from decouple import config, Csv # IMPORTANTE: pip install python-decouple

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =================================================
# SEGURIDAD Y CORE
# =================================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key-dev-only')

# Ahora controlamos esto desde el archivo .env
DEBUG = config('DEBUG', default=False, cast=bool)

# Lee la lista separada por comas desde el .env
#ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())
ALLOWED_HOSTS = ['cfp425.com.ar', 'www.cfp425.com.ar', '127.0.0.1', 'localhost', '*']
# =================================================
# APLICACIONES E INSTALACIÓN
# =================================================
INSTALLED_APPS = [
    'daphne', # Debe estar primero para ASGI
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    
    # Third party apps
    'widget_tweaks',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'import_export',
    'ckeditor',
    'ckeditor_uploader',
    'storages', # AWS/R2
    

    # Local apps
    'cuentas',
    'cursos',
    'documentos',
    'reportes',
    'entregas',
    'blog',
    'anuncios',
    'estudio',
    'mensajes',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'CFP425.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "anuncios.context_processors.anuncio_activo",
            ],
        },
    },
]

WSGI_APPLICATION = 'CFP425.wsgi.application'
ASGI_APPLICATION = 'CFP425.asgi.application'

# =================================================
# BASE DE DATOS & CANALES
# =================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuración de Redis dinámica (Soporta URL completa o host/port)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [config('REDIS_URL', default='redis://127.0.0.1:6379/0')],
        },
    },
}

# =================================================
# AUTENTICACIÓN & ALLAUTH
# =================================================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Config AllAuth
ACCOUNT_FORMS = {'signup': 'cuentas.forms.CustomSignupForm'}
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'user_profile' # Ajustado a tu preferencia
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_UNIQUE_EMAIL = True
# ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_ADAPTER = "cuentas.adapter.CustomSocialAccountAdapter"

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'FETCH_USERINFO' : True,
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}

# =================================================
# INTERNATIONALIZATION
# =================================================
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# =================================================
# ESTÁTICOS & MEDIA (AWS R2)
# =================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage" # <- ESTO ES LO NUEVO
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"
# AWS / Cloudflare R2 Config
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL')

AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_QUERYSTRING_AUTH = True

# Definir almacenamientos
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Configuración CKEditor
CKEDITOR_UPLOAD_PATH = "uploads/ckeditor/"
CKEDITOR_STORAGE_BACKEND = 'storages.backends.s3.S3Storage'
CKEDITOR_CONFIGS = {

    'default': {

        'toolbar': 'Custom',

        'height': 300,

        'width': '100%',

        'toolbar_Custom': [

            ['Styles', 'Format', 'Bold', 'Italic', 'Underline', 'Strike', 'SpellChecker', 'Undo', 'Redo'],

            ['Link', 'Unlink', 'Anchor'],

            ['Image', 'Table', 'HorizontalRule'],

            ['TextColor', 'BGColor'],

            ['Smiley', 'SpecialChar'],

            ['Source'],

            ['NumberedList', 'BulletedList'],

            ['Outdent', 'Indent'],

            ['Blockquote', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],

        ],

        'extraPlugins': ','.join([

            'uploadimage', # si tenés configurada la subida

            'div',

            'autolink',

            'autoembed',

            'embedsemantic',

            'autogrow',

            'widget',

            'lineutils',

            'clipboard',

            'dialog',

            'dialogui',

            'elementspath'

        ]),

    }

}
# =================================================
# EMAIL & TERCEROS
# =================================================

# GEMINI API
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# EMAIL
if DEBUG:
    # En desarrollo a veces es útil ver el mail en consola en vez de mandarlo
    # Cambiá a 'smtp.EmailBackend' si querés probar envío real en debug
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' 
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Mensajes Flash
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
    messages.SUCCESS: 'success',
    messages.INFO: 'info',
    messages.WARNING: 'warning',
}
MESSAGE_LOGIN_REQUIRED = "Por favor, inicia sesión para ver tu perfil."
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'
CSRF_TRUSTED_ORIGINS = ['https://cfp425.com.ar', 'https://www.cfp425.com.ar']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# settings.py

# Permitir que mis páginas se vean en iframes si vienen de mi propio sitio
X_FRAME_OPTIONS = 'SAMEORIGIN'



