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
        "Carregar_campanha/GM/",
        views.carregar_campanha_gm,
        name="carregar_campanha_gm",
    ),
    path(
        "Carregar_campanha/Player/",
        views.carregar_campanha_player,
        name="carregar_campanha_player",
    ),
    # Editar fichas
    path(
        "Fichas/Editar/<int:id>/<str:nome_campanha>/",
        views.editar_fichas,
        name="editar_fichas",
    ),
    # Criar fichas
    path(
        "Campanha/<int:id>/Criar_Ficha/",
        views.criar_ficha_campanha,
        name="criar_ficha_campanha",
    ),
    # Fichas
    path("Fichas/", views.carregar_fichas, name="carregar_fichas"),
    # Menu de fichas GM
    path(
        "Fichas/Menu/GM/<int:campanha_id>", views.menu_fichas_gm, name="menu_fichas_gm"
    ),
    # lista de fichas GM
    path(
        "Fichas/lista/gm/<int:campanha_id>/",
        views.lista_gm_fichas,
        name="lista_gm_fichas",
    ),
    # Get GM characters
    path("api/character/", views.get_character_gm, name="api_get_character_gm"),
    # Save Character
    path(
        "save-character-sheet/", views.save_character_sheet, name="save_character_sheet"
    ),
    # save edit character
    path(
        "save-edit-character-sheet/",
        views.save_edit_character_sheet,
        name="save_edit_character_sheet",
    ),
    # Delete Character
    path(
        "delete-character-sheet-menu/<int:id>/",
        views.delete_sheet_menu,
        name="delete_sheet_menu",
    ),
    # New Asset
    path("add-asset/<int:campanha_id>", views.add_asset, name="add_asset"),
    path(
        "add-asset/<int:campanha_id>/save", views.add_asset_save, name="add_asset_save"
    ),
    # Edit Asset
    path("edit-asset/<int:id>/", views.edit_asset, name="edit_asset"),
    # Delete Asset
    path("delete-asset/<int:id>/", views.delete_asset, name="delete_asset"),
    path("delete-character-sheet/<int:id>/", views.delete_sheet, name="delete_sheet"),
    # interface do jogo
    path(
        "game/<int:campanha_id>/<int:slot>/",
        views.game_interface,
        name="game_interface",
    ),
    # Teste de atributos
    path(
        "teste_atributos/<str:atributo>/<int:nh_attribute>/<int:bonus>/<int:redutor>/<str:name>/",
        views.roll_test_attribute,
        name="teste_atributos",
    ),
    # Teste de ataque
    path(
        "teste_ataque/<str:atributo>/<int:nh_attribute>/<int:bonus>/<int:redutor>/<str:dmg>/<str:name>/",
        views.roll_test_attack,
        name="teste_ataque",
    ),
    # roll d6
    path("rolld6/<int:quantidade>/<str:inc>/", views.roll_d6_interface, name="rolld6"),
    # Leave Game
    path("leave_game/", views.leave_game, name="leave_game"),
    # CHAT
    path("save_message/", views.save_message, name="save_message"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
