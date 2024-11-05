from django.contrib import admin
from .models import RegisterUser, FichaPersonagem  # Importe o modelo RegisterUser


@admin.register(RegisterUser)
class RegisterUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "created_date", "is_staff")
    search_fields = ("username", "email")


@admin.register(FichaPersonagem)
class FichaPersonagemAdmin(admin.ModelAdmin):
    list_display = (
        "nome_jogador",
        "campanha",
        "nome_personagem",
        "total_de_pontos",
    )  # Campos principais para exibição
    search_fields = (
        "nome_jogador",
        "campanha",
        "nome_personagem",
    )  # Campos para a barra de pesquisa
