import secrets
import string

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django_json_widget.widgets import (
    JSONEditorWidget,
)  # Para campos JSON mais amigáveis

from .forms import CharacterSheetForm
from .models import *  # Importa todos os modelos do arquivo models.py


# Registrando o modelo RegisterUser com customização do UserAdmin do Django,
# que automaticamente expõe o link "muda a senha aqui" no formulário de edição
# e a URL /admin/gurps/registeruser/<id>/password/ pra trocar.
@admin.register(RegisterUser)
class RegisterUserAdmin(UserAdmin):
    model = RegisterUser
    list_display = ("username", "email", "created_date", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informações pessoais", {"fields": ("email", "created_date")}),
        (
            "Permissões",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    actions = ["resetar_senha_aleatoria"]

    @admin.action(description="Resetar senha (gera senha aleatória)")
    def resetar_senha_aleatoria(self, request, queryset):
        """Gera uma senha temporária pra cada user selecionado e mostra ao admin."""
        alphabet = string.ascii_letters + string.digits
        resultados = []
        for user in queryset:
            new_pw = "".join(secrets.choice(alphabet) for _ in range(10))
            user.set_password(new_pw)
            user.save(update_fields=["password"])
            resultados.append(f"{user.username}: {new_pw}")
        # Lista as senhas geradas no flash message — o admin precisa copiar
        # e passar pro usuário. Senhas NÃO ficam guardadas em lugar nenhum.
        self.message_user(
            request,
            "Senhas temporárias geradas (copie agora — não vão aparecer de novo): "
            + "  |  ".join(resultados),
            level=messages.WARNING,
        )


# Registrando o modelo Campanha com customização
@admin.register(Campanha)
class CampanhaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dono",
        "nome",
        "pontos_de_ficha",
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
                    "pontos_de_ficha",
                    "pontos_de_desvantagens",
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
        "get_player_name",
        "nome_personagem",
        "get_nome_campanha",
    )
    search_fields = (
        "nome_personagem",
        "info_campanha__player_name",
        "info_campanha__nome_campanha",
    )  # Permite buscar por nome
    list_filter = (
        "id",
        "nome_personagem",
    )  # Filtro para o Admin

    # Método personalizado para exibir o valor da chave 'player_name' do campo JSON 'info_campanha'
    def get_player_name(self, obj):
        return obj.info_campanha.get("player_name", "N/A")

    get_player_name.short_description = "Player Name"

    # Método personalizado para exibir o valor da chave 'campanha' do campo JSON 'info_campanha'
    def get_nome_campanha(self, obj):
        return obj.info_campanha.get("nome_campanha", "N/A")

    get_nome_campanha.short_description = "Nome Campanha"

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


@admin.register(CharacterSheetV2)
class CharacterSheetV2Admin(admin.ModelAdmin):
    """Admin pro modelo novo. JSONFields ganham widget legível."""
    list_display = ("id", "nome_personagem", "campanha", "owner", "is_quick_npc")
    list_filter = ("campanha", "is_quick_npc")
    search_fields = ("id", "nome_personagem", "campanha__nome", "owner__username")
    readonly_fields = ("id",)
    formfield_overrides = {
        # Muitos campos da V2 são JSONField; o widget padrão é textarea sem
        # validação. JSONEditorWidget dá pretty-print + lint.
        # (Aplica via filter no formfield_for_dbfield)
    }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        from django.db.models import JSONField
        if isinstance(db_field, JSONField):
            kwargs["widget"] = JSONEditorWidget
        return super().formfield_for_dbfield(db_field, request, **kwargs)
