from django.db import models

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
    xp_inicial = models.IntegerField(default=0)
    pontos_de_desvantagens = models.IntegerField(default=0)
    xp_acumulado = models.IntegerField(default=0)
    tl = models.IntegerField(default=0)
    fichas_players = models.JSONField(blank=True, null=True)

    descricao = models.TextField(blank=True, null=True)
    regras = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


class FichaPersonagem(models.Model):
    class Meta:
        verbose_name = "Ficha do Personagem"
        verbose_name_plural = "Fichas dos Personagens"

    nome_jogador = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Refere-se ao modelo de usuário personalizado
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    campanha = models.ForeignKey(
        Campanha,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # Outros campos da ficha do personagem
    nome_personagem = models.CharField(max_length=100)
    idade = models.PositiveIntegerField(null=True, blank=True)
    aparencia = models.TextField(blank=True, null=True)
    altura = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )  # Ex.: altura em metros
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )  # Ex.: peso em kg
    tl = models.PositiveIntegerField(null=True, blank=True)

    total_de_pontos = models.IntegerField(default=0)
    pontos_de_experiencia_guardados = models.IntegerField(default=0)

    # Campos de pontos e atributos
    pontos_de_vantagens = models.IntegerField(default=0)
    pontos_de_desvantagens = models.IntegerField(default=0)
    pontos_de_pericias = models.IntegerField(default=0)
    pontos_de_atributos = models.IntegerField(default=0)

    # Ficha
    attributes = models.JSONField(blank=True, null=True)
    subattributes = models.JSONField(blank=True, null=True)
    advantages = models.JSONField(blank=True, null=True)
    disadvantages = models.JSONField(blank=True, null=True)
    skills = models.JSONField(blank=True, null=True)
    equipments = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.nome_personagem} - {self.nome_jogador}"
