"""Views da API V2.

Endpoints mínimos para destravar a SPA (Vite/Tauri) autenticando via
sessão cookie do allauth.
"""

from django.middleware.csrf import get_token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class MeView(APIView):
    """Retorna o usuário autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response(
            {
                "id": u.id,
                "username": u.get_username(),
                "email": getattr(u, "email", ""),
                "is_staff": u.is_staff,
            }
        )


class CsrfView(APIView):
    """Garante que o cookie csrftoken existe no cliente."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class HealthView(APIView):
    """Healthcheck simples (sem autenticação) — útil pra Compose e Tunnel."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})
