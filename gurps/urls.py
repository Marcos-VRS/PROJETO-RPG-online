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
    path(
        "Nova_campanha/lista_campanhas/", views.lista_campanhas, name="lista_campanhas"
    ),
    # Carregar Campanha
    path(
        "Carregar_Campanha/",
        views.carregar_campanha_index,
        name="carregar_campanha_index",
    ),
    path(
        "Campanha/<int:id>/Criar_Ficha/",
        views.criar_ficha_campanha,
        name="criar_ficha_campanha",
    ),
    # Fichas
    path("Fichas/", views.fichas, name="fichas_index"),
    path(
        "save-character-sheet/", views.save_character_sheet, name="save_character_sheet"
    ),
    # Opções
    path("Opções/", views.opcoes, name="opcoes_index"),
    # Chat
    path("chat/<int:campanha_id>/", views.chat_view, name="chat"),
    # Mapas
    path("Mapas/<int:campanha_id>", views.show_mapas, name="mapas"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
