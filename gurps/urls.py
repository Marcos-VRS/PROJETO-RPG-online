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
        "Fichas/Editar/<int:campanha_id>/",
        views.editar_fichas_menu,
        name="editar_fichas_menu",
    ),
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
    # Journal
    path("Journal/<int:campanha_id>/", views.journal, name="journal"),
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
    path(
        "delete-character-sheet-menu/Player/<int:id>/",
        views.delete_sheet_menu_player,
        name="delete_sheet_menu_player",
    ),
    path("delete-character-sheet/<int:id>/", views.delete_sheet, name="delete_sheet"),
    # New Asset
    path("add-asset/<int:campanha_id>", views.add_asset, name="add_asset"),
    path(
        "add-asset/<int:campanha_id>/save", views.add_asset_save, name="add_asset_save"
    ),
    # Edit Asset
    path(
        "edit-asset_menu/<int:campanha_id>/",
        views.edit_asset_menu,
        name="edit_asset_menu",
    ),
    path("edit-asset/<int:asset_id>/", views.edit_asset, name="edit_asset"),
    path(
        "edit-asset/<int:asset_id>/save", views.edit_asset_save, name="edit_asset_save"
    ),
    # Delete Asset
    path(
        "delete-asset-menu/<int:campanha_id>/",
        views.remove_asset_menu,
        name="remove_asset_menu",
    ),
    path("delete-asset/<int:asset_id>/", views.delete_asset, name="delete_asset"),
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
    # Ficha rápida (GM cria/deleta NPCs com poucos campos pra usar em cena)
    path("quick-character/save/", views.save_quick_character, name="save_quick_character"),
    path(
        "quick-character/delete/<int:char_id>/",
        views.delete_quick_character,
        name="delete_quick_character",
    ),
    path(
        "character/<int:char_id>/vitals/",
        views.adjust_character_vitals,
        name="adjust_character_vitals",
    ),
    path(
        "campanha/<int:campanha_id>/pontos/",
        views.atualizar_pontos_campanha,
        name="atualizar_pontos_campanha",
    ),
    # Geração de mapas por IA (Claude headless) — fila + degradação graciosa
    path(
        "map-gen/<int:campanha_id>/request/",
        views.map_gen_request,
        name="map_gen_request",
    ),
    path(
        "map-gen/status/<int:req_id>/",
        views.map_gen_status,
        name="map_gen_status",
    ),
    path("journal-data/<int:campanha_id>/", views.journal_data, name="journal_data"),
    path("map-gen/<int:campanha_id>/list/", views.map_gen_list, name="map_gen_list"),
    path("map-gen/svg/<int:req_id>/", views.map_gen_svg, name="map_gen_svg"),
    path("map-gen/<int:req_id>/approve/", views.map_gen_approve, name="map_gen_approve"),
    path("map-gen/<int:req_id>/discard/", views.map_gen_discard, name="map_gen_discard"),
    # Estúdio de Imagem (ComfyUI local — personagens + mapas)
    path("imagegen/<int:campanha_id>/status/", views.imagegen_status, name="imagegen_status"),
    path("imagegen/<int:campanha_id>/request/", views.imagegen_request, name="imagegen_request"),
    path("imagegen/<int:campanha_id>/list/", views.imagegen_list, name="imagegen_list"),
    path("imagegen/<int:campanha_id>/journal/", views.imagegen_journal, name="imagegen_journal"),
    path("imagegen/req/<int:req_id>/status/", views.imagegen_req_status, name="imagegen_req_status"),
    path("imagegen/png/<int:req_id>/", views.imagegen_png, name="imagegen_png"),
    path("imagegen/<int:req_id>/approve/", views.imagegen_approve, name="imagegen_approve"),
    path("imagegen/<int:req_id>/discard/", views.imagegen_discard, name="imagegen_discard"),
    path("Campanha/<int:campanha_id>/estudio-imagem/", views.imagegen_studio, name="imagegen_studio"),
    path("Campanha/<int:campanha_id>/gerador-mapa/", views.mapgen_studio, name="mapgen_studio"),
    path("Campanha/<int:campanha_id>/estudio-video/", views.videogen_studio, name="videogen_studio"),
    path("videogen/<int:campanha_id>/request/", views.videogen_request, name="videogen_request"),
    path("videogen/<int:campanha_id>/list/", views.videogen_list, name="videogen_list"),
    path("videogen/<int:campanha_id>/music/", views.videogen_music, name="videogen_music"),
    path("videogen/mp4/<int:req_id>/", views.videogen_mp4, name="videogen_mp4"),
    path("videogen/<int:req_id>/approve/", views.videogen_approve, name="videogen_approve"),
    path("videogen/<int:req_id>/discard/", views.videogen_discard, name="videogen_discard"),
    path("videogen/<int:req_id>/resume/", views.videogen_resume, name="videogen_resume"),
    path("videogen/<int:req_id>/pause/", views.videogen_pause, name="videogen_pause"),
    # Editor de beats (cena por cena na timeline do áudio)
    path("videogen/<int:campanha_id>/project/create/", views.videogen_project_create, name="videogen_project_create"),
    path("videogen/<int:campanha_id>/projects/", views.videogen_projects, name="videogen_projects"),
    path("videogen/project/<int:req_id>/", views.videogen_project_detail, name="videogen_project_detail"),
    path("videogen/project/<int:req_id>/update/", views.videogen_project_update, name="videogen_project_update"),
    path("videogen/project/<int:req_id>/beat/add/", views.videogen_beat_add, name="videogen_beat_add"),
    path("videogen/project/<int:req_id>/beat/reorder/", views.videogen_beat_reorder, name="videogen_beat_reorder"),
    path("videogen/project/<int:req_id>/assemble/", views.videogen_project_assemble, name="videogen_project_assemble"),
    path("videogen/beat/<int:beat_id>/update/", views.videogen_beat_update, name="videogen_beat_update"),
    path("videogen/beat/<int:beat_id>/delete/", views.videogen_beat_delete, name="videogen_beat_delete"),
    path("videogen/beat/<int:beat_id>/generate/", views.videogen_beat_generate, name="videogen_beat_generate"),
    path("videogen/beat/<int:beat_id>/mp4/", views.videogen_beat_mp4, name="videogen_beat_mp4"),
    path("videogen/beat/<int:beat_id>/edit/", views.videogen_beat_edit, name="videogen_beat_edit"),
    path("videogen/beat/<int:beat_id>/edit/approve/", views.videogen_beat_edit_approve, name="videogen_beat_edit_approve"),
    path("videogen/beat/<int:beat_id>/edit/discard/", views.videogen_beat_edit_discard, name="videogen_beat_edit_discard"),
    path("videogen/beat/<int:beat_id>/edit/revert/", views.videogen_beat_edit_revert, name="videogen_beat_edit_revert"),
    path("videogen/beat/<int:beat_id>/edit/image/", views.videogen_beat_edit_image, name="videogen_beat_edit_image"),
    path("videogen/beat/<int:beat_id>/caption/", views.videogen_beat_caption, name="videogen_beat_caption"),
    # GM Tool Box (biblioteca pessoal do user)
    path("toolbox/", views.toolbox_list, name="toolbox_list"),
    path("toolbox/create/", views.toolbox_create, name="toolbox_create"),
    path("toolbox/<int:item_id>/delete/", views.toolbox_delete, name="toolbox_delete"),

    # =========================================================================
    # CharacterSheetV2 (ficha nova, 2026-05-16)
    # =========================================================================
    path("v2/Campanha/<int:campanha_id>/Criar_Ficha/", views.criar_v2, name="criar_v2"),
    path("v2/Ficha/<int:id>/Editar/", views.editar_v2, name="editar_v2"),
    path("v2/Ficha/<int:id>/Ver/", views.ver_v2, name="ver_v2"),
    path("v2/Ficha/<int:id>/Delete/", views.delete_v2, name="delete_v2"),
    path("v2/Campanha/<int:campanha_id>/Fichas/GM/", views.lista_v2_gm, name="lista_v2_gm"),
    path("v2/Campanha/<int:campanha_id>/Fichas/Player/", views.lista_v2_player, name="lista_v2_player"),
    path("v2/api/compute-secondary/", views.api_compute_secondary, name="api_compute_secondary_v2"),
    path("v2/api/catalog/advantages/", views.api_catalog_advantages, name="api_catalog_advantages_v2"),
    path("v2/api/catalog/disadvantages/", views.api_catalog_disadvantages, name="api_catalog_disadvantages_v2"),
    path("v2/api/catalog/modifiers/", views.api_catalog_modifiers, name="api_catalog_modifiers_v2"),
    path("v2/api/catalog/skills/", views.api_catalog_skills, name="api_catalog_skills_v2"),
    path("v2/api/Ficha/<int:id>/quickadd/<str:kind>/",
         views.api_quick_add, name="api_quick_add_v2"),
    path("v2/api/Ficha/<int:id>/quickremove/<str:kind>/<int:index>/",
         views.api_quick_remove, name="api_quick_remove_v2"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
