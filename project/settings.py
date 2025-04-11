"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 5.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-&koef1^d04z2y($vy5&$&3bg-2*kv_-_*v$ru5hnb1(ddhs7y&"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["roll3d6rpg.com", "www.roll3d6rpg.com", "127.0.0.1", "localhost"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "gurps",
    "django.contrib.sites",  # Necessário para Allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",  # Para autenticação social
    "allauth.socialaccount.providers.google",
    "django_htmx",
    "channels",
    "corsheaders",  # Certifique-se de que o CORS está instalado
]

# Configuração dos backends de autenticação
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # Backend de autenticação padrão do Django
    "allauth.account.auth_backends.AuthenticationBackend",  # Backend do django-allauth
]

# Configurações de conta
ACCOUNT_EMAIL_REQUIRED = True  # Tornar o e-mail obrigatório para o cadastro
ACCOUNT_USERNAME_REQUIRED = False  # Desabilitar a exigência de nome de usuário
ACCOUNT_AUTHENTICATION_METHOD = (
    "email"  # Usar o e-mail para autenticação (em vez do nome de usuário)
)
ACCOUNT_EMAIL_VERIFICATION = (
    "optional"  # Pode ser 'mandatory' para exigir verificação de e-mail
)


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Adicionando o middleware do CORS
]

ROOT_URLCONF = "project.urls"

SITE_ID = 1

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "base_templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# WSGI_APPLICATION = "project.wsgi.application"

ASGI_APPLICATION = "project.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "gurps.RegisterUser"

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

STATICFILES_DIRS = [BASE_DIR / "base_static"]

STATIC_ROOT = BASE_DIR / "static"  # collectstatic


STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

CSRF_TRUSTED_ORIGINS = [
    "https://roll3d6rpg.com",
    "https://www.roll3d6rpg.com",
]

CORS_ALLOWED_ORIGINS = [
    "https://roll3d6rpg.com",
    "https://www.roll3d6rpg.com",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


try:
    from project.local_settings import *
except ImportError:
    ...
