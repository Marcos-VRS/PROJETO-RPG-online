"""
Django settings for project project.

Variáveis de ambiente controlam DB, cache, channels, secrets e CORS.
Em dev (WSL2 local) e prod (GCP VM) usamos o MESMO stack:
Postgres + pgvector + Redis. Sem SQLite em nenhum ambiente.

Override local pontual (paths, debug, etc.) continua via project/local_settings.py.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key: str, default: str | None = None, required: bool = False) -> str:
    """Lê variável de ambiente; falha em prod se obrigatória estiver faltando."""
    val = os.environ.get(key, default)
    if required and not val:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {key}")
    return val


def env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def env_list(key: str, default: list[str] | None = None) -> list[str]:
    raw = os.environ.get(key, "")
    if not raw:
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]


# ------------------------------------------------------------------------
# Core
# ------------------------------------------------------------------------

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-&koef1^d04z2y($vy5&$&3bg-2*kv_-_*v$ru5hnb1(ddhs7y&",
)

DEBUG = env_bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    default=[
        "roll3d6rpg.com",
        "www.roll3d6rpg.com",
        "127.0.0.1",
        "localhost",
    ],
)


# ------------------------------------------------------------------------
# Apps
# ------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "gurps",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django_htmx",
    "channels",
    "corsheaders",
    "rest_framework",
    "rag",
    "api",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "optional"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
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


ASGI_APPLICATION = "project.asgi.application"


# ------------------------------------------------------------------------
# Channels / Redis
# ------------------------------------------------------------------------

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env("REDIS_HOST", "127.0.0.1"), int(env("REDIS_PORT", "6379")))],
        },
    },
}


# ------------------------------------------------------------------------
# Database — Postgres em dev e prod (paridade total)
# ------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "roll3d6_dev"),
        "USER": env("POSTGRES_USER", "roll3d6_dev"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "127.0.0.1"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}


# ------------------------------------------------------------------------
# Auth password validators
# ------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "gurps.RegisterUser"


# ------------------------------------------------------------------------
# I18N
# ------------------------------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------------------
# Static / media
# ------------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "base_static"]
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ------------------------------------------------------------------------
# CORS / CSRF
# ------------------------------------------------------------------------

# Origens onde a SPA (Vite/Tauri dev) e o site em produção rodam.
# Em dev local: localhost:5173 (Vite) e localhost:1420 (Tauri dev).
# Em prod: domínio Cloudflare.
_DEFAULT_CORS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:1420",
    "http://127.0.0.1:1420",
    "https://roll3d6rpg.com",
    "https://www.roll3d6rpg.com",
]

CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS", default=_DEFAULT_CORS)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=_DEFAULT_CORS,
)


# ------------------------------------------------------------------------
# DRF
# ------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}


# ------------------------------------------------------------------------
# RAG / Ollama
# ------------------------------------------------------------------------

OLLAMA_URL = env("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")


# ------------------------------------------------------------------------
# Misc
# ------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Override local opcional (paths de dev, etc.). Não commitar.
try:
    from project.local_settings import *  # noqa: F401,F403
except ImportError:
    pass
