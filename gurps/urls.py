from django.urls import path
from gurps import views
from django.conf import settings
from django.conf.urls.static import static


app_name = "gurps"

urlpatterns = [
    # Register
    path("register/", views.register_view, name="register"),
    # Login/Logout
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Index
    path("", views.index, name="index"),
    # Nova Campanha
    path("Nova_Campanha/", views.nova_campanha, name="nova_campanha_index"),
    path("Nova_campanha/Criar_Campanha/", views.criar_campanha, name="criar_campanha"),
    # Carregar Campanha
    path("Carregar_Campanha/", views.carregar_campanha, name="carregar_campanha_index"),
    # Fichas
    path("Fichas/", views.fichas, name="fichas_index"),
    # Opções
    path("Opções/", views.opcoes, name="opcoes_index"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
