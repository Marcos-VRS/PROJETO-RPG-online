from django.contrib import admin
from .models import *  # Importa todos os modelos do arquivo models.py
from .forms import CharacterSheetForm
from django_json_widget.widgets import (
    JSONEditorWidget,
)  # Para campos JSON mais amigáveis


# Registrando o modelo RegisterUser com customização
@admin.register(RegisterUser)
class RegisterUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "created_date", "is_staff")
    search_fields = ("username", "email")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "email",
                    "created_date",
                    "is_staff",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )


# Registrando o modelo Campanha com customização
@admin.register(Campanha)
class CampanhaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dono",
        "nome",
        "xp_inicial",
        "xp_acumulado",
        "pontos_de_desvantagens",
        "tl",
    )
    search_fields = ("nome",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "dono",
                    "nome",
                    "xp_inicial",
                    "pontos_de_desvantagens",
                    "xp_acumulado",
                    "tl",
                    "fichas_players",
                    "descricao",
                    "regras",
                    "imagem",
                )
            },
        ),
    )


# Registrando o modelo CharacterSheet com customização
class CharacterSheetAdmin(admin.ModelAdmin):
    form = CharacterSheetForm  # Usando um form personalizado, se necessário
    list_display = (
        "nome_personagem",
        "money",
        "background",
        "photo",  # Exibe esses campos na lista do Admin
    )
    search_fields = ("nome_personagem",)  # Permite buscar por nome
    list_filter = ("money",)  # Filtro para o campo 'money' no Admin

    # Personalizando o formulário de edição
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "info_campanha",
                    "nome_personagem",
                    "aparencia_idade",
                    "background",
                    "photo",
                    "money",
                )
            },
        ),
        (
            "Pontos",
            {"fields": ("pontos_soma",)},  # Exibe 'pontos_soma' no formulário de edição
        ),
        (
            "Atributos",
            {
                "fields": (
                    "atributos",
                    "sub_attributes",
                )  # Exibe 'atributos' e 'sub_attributes' no formulário de edição
            },
        ),
        (
            "Vantagens e Desvantagens",
            {
                "fields": (
                    "advantages",
                    "disadvantages",
                )  # Exibe 'advantages' e 'disadvantages' no formulário de edição
            },
        ),
        ("Perícias", {"fields": ("skills",)}),  # Exibe 'skills' no formulário de edição
        (
            "Equipamentos",
            {
                "fields": (
                    "equipment_melee",
                    "equipment_ranged",
                    "equipment_armor",
                )  # Exibe equipamentos no formulário de edição
            },
        ),
        (
            "Manobras",
            {
                "fields": (
                    "maneuvers_melee",
                    "maneuvers_ranged",
                    "maneuvers_defense",
                )  # Exibe manobras no formulário de edição
            },
        ),
    )


# Registrando o modelo CampanhaAssets com customização
@admin.register(CampanhaAssets)
class CampanhaAssetsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slot", "campanha", "description", "image")
    search_fields = ("id", "name", "campanha__nome")


# Registrando o modelo Message com customização
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "campanha", "content", "timestamp")
    search_fields = ("user__username", "campanha__nome", "content")


# Registrando o modelo CharacterSheet com a customização específica
admin.site.register(CharacterSheet, CharacterSheetAdmin)
