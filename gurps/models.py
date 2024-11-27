from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class RegisterUser(AbstractUser):

    created_date = models.DateField(default=timezone.now)

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
    nome = models.CharField(max_length=100)
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campanhas",
        blank=True,
        null=True,
    )

    xp_inicial = models.IntegerField(default=0)
    pontos_de_desvantagens = models.IntegerField(default=0)
    xp_acumulado = models.IntegerField(default=0)
    tl = models.IntegerField(default=0)
    fichas_players = models.JSONField(blank=True, null=True)

    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    regras = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to="campanhas/", blank=True, null=True)

    def __str__(self):
        return self.nome


class CharacterSheet(models.Model):
    # Informações básicas
    nome_personagem = models.CharField(max_length=255, blank=True, null=True)
    aparencia_idade = models.JSONField(blank=True, null=True)  # JSON opcional

    # Pontos
    points_summary = models.JSONField(blank=True, null=True)

    # Atributos
    attributes = models.JSONField(blank=True, null=True)
    sub_attributes = models.JSONField(blank=True, null=True)

    # Vantagens e desvantagens
    advantages = models.JSONField(blank=True, null=True)
    disadvantages = models.JSONField(blank=True, null=True)

    # Perícias
    skills = models.JSONField(blank=True, null=True)

    # Dinheiro e background
    money = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True, null=True
    )
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
