"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as static_serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),  # API V2 (SPA / Tauri)
    # path("rag/", include("rag.urls")),  # hibernado — ver docs/RAG_ARCHITECTURE.md
    path("", include("gurps.urls")),  # inclui URLs do app "gurps"
    path("accounts/", include("allauth.urls")),  # Inclui as URLs do allauth
]

# No modo desktop, daphne é o único processo servindo HTTP — não há nginx
# pra entregar mídia. Como DEBUG=False, o helper `static()` do Django não
# funciona; usamos `django.views.static.serve` direto. Em produção GCP,
# nginx cuida disso, então só ativamos esta rota no modo desktop.
if getattr(settings, "DESKTOP_HOME", None):
    urlpatterns.append(
        re_path(r"^media/(?P<path>.*)$", static_serve, {"document_root": settings.MEDIA_ROOT})
    )
