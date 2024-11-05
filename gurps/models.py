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
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


class FichaPersonagem(models.Model):
    class Meta:
        verbose_name = "Ficha do Personagem"
        verbose_name_plural = "Fichas dos Personagens"

    nome_jogador = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Refere-se ao modelo de usuário personalizado
        on_delete=models.CASCADE,
        editable=False,  # Impede edição direta do campo
    )

    campanha = models.ForeignKey(
        Campanha,
        on_delete=models.CASCADE,
        editable=False,  # O backend definirá a campanha automaticamente
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
    total_de_pontos = models.IntegerField(default=0)
    pontos_de_experiencia_guardados = models.IntegerField(default=0)

    # Campos de pontos e atributos
    pontos_de_vantagens = models.IntegerField(default=0)
    pontos_de_desvantagens = models.IntegerField(default=0)
    pontos_de_pericias = models.IntegerField(default=0)
    pontos_de_atributos = models.IntegerField(default=0)

    # Exemplo de atributos do personagem
    st = models.IntegerField(default=10)  # Força base
    xpst = models.IntegerField(default=0)  # Experiência em força

    dx = models.IntegerField(default=10)  # Destreza base
    xpdx = models.IntegerField(default=0)  # Experiência em destreza

    iq = models.IntegerField(default=10)  # Inteligência base
    xpiq = models.IntegerField(default=0)  # Experiência em inteligência

    ht = models.IntegerField(default=10)  # Saúde base
    xpht = models.IntegerField(default=0)  # Experiência em saúde

    damage = models.CharField(max_length=50, blank=True, null=True)
    basic_lift_lbs = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    hp = models.IntegerField(default=10)  # Pontos de vida
    will = models.IntegerField(default=10)  # Vontade
    perception = models.IntegerField(default=10)  # Percepção
    fp = models.IntegerField(default=10)  # Pontos de fadiga
    basic_speed = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    basic_move = models.IntegerField(default=5)  # Movimento básico

    advantages = models.TextField(blank=True, null=True)
    disadvantages = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    equipments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nome_personagem} - {self.nome_jogador}"
