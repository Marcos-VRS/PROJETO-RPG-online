"""
Django settings for project project.

Padrão: modo desktop/dev com SQLite e channel layer in-memory.
Stack V2 (Docker Compose): definir POSTGRES_DB (Postgres) e ROLL3D6_MODE=gcp_legacy (Redis).

Override local pontual (paths, debug, etc.) continua via project/local_settings.py.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Modo desktop: o launcher exporta ROLL3D6_DESKTOP_HOME apontando pra
# %APPDATA%\roll3d6, onde ficam banco, mídia e SECRET_KEY do usuário final.
# Quando ausente (dev/CI), tudo cai em BASE_DIR como antes.
_DESKTOP_HOME = os.environ.get("ROLL3D6_DESKTOP_HOME")
DESKTOP_HOME = Path(_DESKTOP_HOME) if _DESKTOP_HOME else None
if DESKTOP_HOME:
    DESKTOP_HOME.mkdir(parents=True, exist_ok=True)
    (DESKTOP_HOME / "media").mkdir(parents=True, exist_ok=True)
    (DESKTOP_HOME / "logs").mkdir(parents=True, exist_ok=True)


def env(key: str, default: str | None = None, required: bool = False) -> str:
    """Lê variável de ambiente; falha em prod se obrigatória estiver faltando."""
    val = os.environ.get(key, default)
    if required and not val:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {key}")
    return val


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECRET_KEY:
# - Modo desktop: lido de %APPDATA%\roll3d6\secret.key (gerado pelo launcher na primeira execução).
# - Modo dev: valor fixo abaixo (NÃO use em produção real).
if DESKTOP_HOME and (DESKTOP_HOME / "secret.key").exists():
    SECRET_KEY = (DESKTOP_HOME / "secret.key").read_text(encoding="utf-8").strip()
else:
    SECRET_KEY = "django-insecure-&koef1^d04z2y($vy5&$&3bg-2*kv_-_*v$ru5hnb1(ddhs7y&"

# DEBUG: ligado em dev, desligado no app desktop.
DEBUG = DESKTOP_HOME is None

# ALLOWED_HOSTS: no desktop deixamos aberto porque o túnel Cloudflare usa
# subdomínios aleatórios *.trycloudflare.com. Segurança vem do fato de só
# quem tem a URL pública entrar; o tráfego local é só localhost.
if DESKTOP_HOME:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = [
        "roll3d6rpg.com",
        "www.roll3d6rpg.com",
        "127.0.0.1",
        "localhost",
    ]


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
# Apps
# ------------------------------------------------------------------------

INSTALLED_APPS = [
    # daphne deve vir ANTES de django.contrib.staticfiles pra patchar runserver
    # e habilitar WebSocket no modo dev. Sem isso, /ws/ retorna 404. Em produção
    # (.exe bundleado) daphne é lançado como processo separado, então isso só
    # afeta `python manage.py runserver`.
    "daphne",
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
    "corsheaders",  # Certifique-se de que o CORS está instalado
    "django_json_widget",  # JSONEditorWidget no admin (fichas V2/MapState).
    #                        Sem isso o template django_json_widget.html não é
    #                        achado e o admin da ficha V2 dá 500.
    # "rag",  # hibernado desde 2026-05-14 (pivô desktop): depende de pgvector.
    #          ver docs/RAG_ARCHITECTURE.md
    "rest_framework",  # API V2 (SPA)
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

# Em DEBUG=False (modo desktop, GCP), Django auto-aplica cached.Loader sobre
# os loaders default. Isso cacheia template em memória — bom em produção
# bundleada (PyInstaller), MAU em modo desktop dev onde editamos templates
# e esperamos que reflita sem restart. Solução: detectar modo bundleado
# (sys.frozen) e usar cache só nele.
_TEMPLATE_LOADERS = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
if getattr(sys, "frozen", False):
    # Modo bundleado: cache de template OK (não há edits após build).
    _TEMPLATE_LOADERS = [("django.template.loaders.cached.Loader", _TEMPLATE_LOADERS)]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "base_templates"],
        # APP_DIRS=False quando setamos loaders manualmente (Django exige).
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": _TEMPLATE_LOADERS,
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

# Channel layer — InMemory por default (modo desktop, sem Redis).
# Para o ambiente legado GCP que ainda usa Redis, exportar ROLL3D6_MODE=gcp_legacy.
if os.environ.get("ROLL3D6_MODE") == "gcp_legacy":
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [(env("REDIS_HOST", "127.0.0.1"), int(env("REDIS_PORT", "6379")))]},
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }


# ------------------------------------------------------------------------
# Database — SQLite (desktop/dev). Postgres é opt-in via POSTGRES_DB (stack V2/Docker).
# ------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": (DESKTOP_HOME / "data.sqlite3") if DESKTOP_HOME else (BASE_DIR / "db.sqlite3"),
    }
}

if os.environ.get("POSTGRES_DB"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "roll3d6_dev"),
        "USER": env("POSTGRES_USER", "roll3d6_dev"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "127.0.0.1"),
        "PORT": env("POSTGRES_PORT", "5432"),
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

STATIC_ROOT = BASE_DIR / "static"  # collectstatic


if DESKTOP_HOME:
    if getattr(sys, "frozen", False):
        # Modo bundleado (PyInstaller): os estáticos foram coletados em
        # build-time via `collectstatic` e ficam em _MEIPASS\static.
        # Whitenoise serve a partir daí — caminho mais rápido e confiável
        # do que o modo `USE_FINDERS` (que depende de __path__ dos apps).
        STATIC_ROOT = Path(sys._MEIPASS) / "static"  # type: ignore[attr-defined]
        STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
    else:
        # Modo dev (rodando `python -m desktop.launcher` direto do venv):
        # Whitenoise serve de STATICFILES_DIRS via finders, sem collectstatic.
        STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
        WHITENOISE_USE_FINDERS = True
        WHITENOISE_AUTOREFRESH = True
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"

MEDIA_ROOT = (DESKTOP_HOME / "media") if DESKTOP_HOME else (BASE_DIR / "media")

# CSRF e CORS:
# - Modo desktop: o launcher injeta a URL pública do Cloudflare em
#   ROLL3D6_TUNNEL_URL após capturá-la, e essa URL é incluída nos trusted origins.
# - Modo dev/GCP: lista fixa.
_TUNNEL_URL = os.environ.get("ROLL3D6_TUNNEL_URL", "").strip()

if DESKTOP_HOME:
    CSRF_TRUSTED_ORIGINS = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        # Cloudflare Quick Tunnel publica em *.trycloudflare.com (HTTPS). URL
        # é dinâmica por sessão; aceitamos qualquer subdomínio pra não depender
        # de injeção de env var no subprocess do daphne (que é spawned ANTES
        # do tunnel capturar a URL, então env nunca chega lá).
        "https://*.trycloudflare.com",
        "https://*.cfargotunnel.com",
    ]
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^https://[a-z0-9-]+\.trycloudflare\.com$",
        r"^https://[a-z0-9-]+\.cfargotunnel\.com$",
    ]
    CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]
    # Cloudflare termina TLS e nos repassa via X-Forwarded-Proto: https.
    # Sem isso, Django acha que é HTTP e bloqueia request_is_secure().
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    if _TUNNEL_URL:
        if _TUNNEL_URL not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(_TUNNEL_URL)
        if _TUNNEL_URL not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(_TUNNEL_URL)
else:
    CSRF_TRUSTED_ORIGINS = [
        "https://roll3d6rpg.com",
        "https://www.roll3d6rpg.com",
    ]
    CORS_ALLOWED_ORIGINS = [
        "https://roll3d6rpg.com",
        "https://www.roll3d6rpg.com",
    ]

# SPA V2 (Vite/Tauri dev) — origens extras, ativas em qualquer modo.
_SPA_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:1420",
    "http://127.0.0.1:1420",
]
for _origin in _SPA_DEV_ORIGINS:
    if _origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(_origin)
    if _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)
CORS_ALLOW_CREDENTIALS = True


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
