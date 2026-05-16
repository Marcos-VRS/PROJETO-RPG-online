"""ASGI entrypoint do projeto.

Ordem dos imports importa: Django apps precisam estar carregados ANTES de
qualquer `from gurps.models import ...`. Por isso:

1. Setar DJANGO_SETTINGS_MODULE
2. Chamar get_asgi_application() (faz django.setup() internamente)
3. SÓ DEPOIS importar gurps.routing (que importa consumers → models)

Trocar essa ordem reproduz `AppRegistryNotReady: Apps aren't loaded yet.`
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.core.asgi import get_asgi_application  # noqa: E402

# Boot Django ANTES de importar qualquer coisa que toque models.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402
import gurps.routing  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(gurps.routing.websocket_urlpatterns)
        ),
    }
)
