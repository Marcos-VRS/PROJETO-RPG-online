from django.contrib import admin
from .models import RegisterUser, Campanha, FichaPersonagem


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
                    "nome",
                    "xp_inicial",
                    "pontos_de_desvantagens",
                    "xp_acumulado",
                    "tl",
                    "fichas_players",
                    "descricao",
                    "regras",
                )
            },
        ),
    )


@admin.register(FichaPersonagem)
class FichaPersonagemAdmin(admin.ModelAdmin):
    list_display = (
        "nome_jogador",
        "campanha",
        "nome_personagem",
        "total_de_pontos",
        "pontos_de_experiencia_guardados",
    )
    search_fields = ("nome_jogador__username", "campanha__nome", "nome_personagem")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "nome_jogador",
                    "campanha",
                    "nome_personagem",
                    "idade",
                    "aparencia",
                    "altura",
                    "peso",
                    "tl",
                    "total_de_pontos",
                    "pontos_de_experiencia_guardados",
                    "pontos_de_vantagens",
                    "pontos_de_desvantagens",
                    "pontos_de_pericias",
                    "pontos_de_atributos",
                    "attributes",
                    "subattributes",
                    "advantages",
                    "disadvantages",
                    "skills",
                    "equipments",
                )
            },
        ),
    )
