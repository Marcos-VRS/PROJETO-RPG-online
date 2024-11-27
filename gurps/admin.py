from django.contrib import admin
from .models import RegisterUser, Campanha
from .models import CharacterSheet
from .forms import CharacterSheetForm
from django import forms
from django_json_widget.widgets import (
    JSONEditorWidget,
)  # Para campos JSON mais amigáveis


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


@admin.register(Campanha)
class CampanhaAdmin(admin.ModelAdmin):
    list_display = (
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


# Customizando a exibição do modelo no Admin
class CharacterSheetAdmin(admin.ModelAdmin):
    form = CharacterSheetForm
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
            {
                "fields": (
                    "points_summary",
                )  # Exibe 'points_summary' no formulário de edição
            },
        ),
        (
            "Atributos",
            {
                "fields": (
                    "attributes",
                    "sub_attributes",
                )  # Exibe 'attributes' e 'sub_attributes' no formulário de edição
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


# Registrando o modelo no Admin
admin.site.register(CharacterSheet, CharacterSheetAdmin)
