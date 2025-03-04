from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import FileExtensionValidator


class RegisterUser(AbstractUser):

    created_date = models.DateField(default=timezone.now)

    username = models.CharField(
        max_length=20,
        unique=True,
        help_text="Digite um nome de usuário único para login com no máximo 20 caracteres.",
        verbose_name="Nome de usuário",
    )

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",  # Nome único para evitar conflitos
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",  # Nome único para evitar conflitos
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def __str__(self) -> str:
        return self.username


class Campanha(models.Model):
    nome = models.CharField(max_length=30, unique=True)
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campanhas",
        blank=True,
        null=True,
    )

    pontos_de_ficha = models.IntegerField(default=0)
    pontos_de_desvantagens = models.IntegerField(default=0)
    xp_acumulado = models.IntegerField(default=0)
    tl = models.IntegerField(default=0)
    fichas_players = models.JSONField(blank=True, null=True)

    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    regras = models.TextField(blank=True, null=True)
    imagem = models.ImageField(
        upload_to="campanhas/",
        blank=False,
        null=False,  # Permite nulo no banco, mas não no form
        default=None,  # Evita que Django preencha com string vazia
    )

    def __str__(self):
        return self.nome


class CampanhaAssets(models.Model):
    campanha = models.ForeignKey(
        Campanha,
        on_delete=models.CASCADE,
        related_name="assets",
        blank=True,
        null=True,
        max_length=30,
    )
    slot = models.IntegerField(default=1)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="campanhas_assets/", blank=True, null=True)

    def __str__(self):
        return self.name


class CharacterSheet(models.Model):

    # Informações básicas
    info_campanha = models.JSONField(blank=True, null=True)  # JSON opcional

    nome_personagem = models.CharField(
        max_length=30, blank=True, null=True, unique=True
    )
    aparencia_idade = models.JSONField(blank=True, null=True)  # JSON opcional

    # Pontos
    pontos_soma = models.JSONField(blank=True, null=True)

    # Atributos
    atributos = models.JSONField(blank=True, null=True)
    sub_attributes = models.JSONField(blank=True, null=True)

    # Vantagens e desvantagens
    advantages = models.JSONField(blank=True, null=True)
    disadvantages = models.JSONField(blank=True, null=True)

    # Perícias
    skills = models.JSONField(blank=True, null=True)

    # Dinheiro e background
    money = models.CharField(max_length=20, blank=True, null=True)

    background = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to="character_photos/", blank=True, null=True)

    # Equipamentos
    equipment_melee = models.JSONField(blank=True, null=True)
    equipment_ranged = models.JSONField(blank=True, null=True)
    equipment_armor = models.JSONField(blank=True, null=True)

    # Manobras
    maneuvers_melee = models.JSONField(blank=True, null=True)
    maneuvers_ranged = models.JSONField(blank=True, null=True)
    maneuvers_defense = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.nome_personagem or "Ficha Sem Nome"


class Message(models.Model):
    user = models.ForeignKey(RegisterUser, on_delete=models.CASCADE)
    campanha = models.ForeignKey(
        Campanha,
        on_delete=models.CASCADE,
        related_name="mensagens",  # Permite acessar mensagens relacionadas à campanha
        blank=True,
        null=True,
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        campanha_nome = self.campanha.nome if self.campanha else "Sem Campanha"
        return f"[{campanha_nome}] {self.user.username}: {self.content}"
