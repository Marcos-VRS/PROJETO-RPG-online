from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify


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

    descricao = models.TextField(
        max_length=20000, blank=True, null=True, verbose_name="Descrição"
    )
    regras = models.TextField(blank=True, null=True, max_length=20000)
    imagem = models.ImageField(
        upload_to="campanhas/",
        blank=False,
        null=False,  # Permite nulo no banco, mas não no form
        default=None,  # Evita que Django preencha com string vazia
    )

    # Estado da cena ativa (controlado pelo GM, espelhado aos players via WS).
    # Estrutura forward-compatible:
    #   {
    #     "active": {"name": "...", "present_character_ids": [int, ...], "notes": "..."},
    #     "presets": [ {"name": ..., "present_character_ids": [...], "notes": ...}, ... ]
    #   }
    # Quando vazio (default), todos os personagens da campanha são tratados como presentes.
    scene_state = models.JSONField(blank=True, null=True, default=dict)

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
    show = models.BooleanField(default=True)
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True, null=True, max_length=20000)
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

    # Estado de jogo (HP/FP atuais e outros valores dinâmicos que mudam durante
    # a sessão). Estrutura esperada: {"hp_atual": int, "fp_atual": int, ...}.
    # Quando vazio, o front assume hp_atual = sub_attributes.hp (barra cheia).
    # Adicionar valores novos aqui é seguro — JSONField nunca quebra schema.
    runtime_stats = models.JSONField(blank=True, null=True, default=dict)

    def __str__(self):
        return self.nome_personagem or "Ficha Sem Nome"


class CharacterSheetV2(models.Model):
    """Nova ficha (2026-05-16).

    Diferença vs CharacterSheet (V1, legado):
    - ForeignKey real para Campanha + RegisterUser (dono)
    - Secundárias (HP/FP/Will/Per/Speed/Move/Dodge/BL) sempre calculadas via
      sheet_v2_calc.compute_secondary() — não armazenadas redundantemente
    - Vantagens/Desvantagens/Skills referenciam ids do catálogo em gurps/data/
    - Pontos auto-calculados (points_spent) com breakdown
    """

    campanha = models.ForeignKey(
        Campanha, on_delete=models.CASCADE, related_name="sheets_v2"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="sheets_v2", blank=True, null=True,
    )

    nome_personagem = models.CharField(max_length=60, blank=True)
    aparencia = models.TextField(blank=True)
    idade = models.CharField(max_length=20, blank=True)
    background = models.TextField(blank=True)
    photo = models.ImageField(upload_to="character_photos_v2/", blank=True, null=True)
    money = models.CharField(max_length=40, blank=True)

    # Atributos primários: {"st": 10, "dx": 10, "iq": 10, "ht": 10}
    primary_attributes = models.JSONField(default=dict, blank=True)

    # Modificadores opcionais nas secundárias (jogador pode comprar HP extra etc.)
    # Ex: {"hp": +2, "will": -1, "basic_speed": 0.25}
    secondary_modifiers = models.JSONField(default=dict, blank=True)

    # Vantagens: [{"id": "combat_reflexes", "level": 1, "modifiers": [], "custom_cost": null, "notes": ""}, ...]
    advantages = models.JSONField(default=list, blank=True)
    disadvantages = models.JSONField(default=list, blank=True)

    # Skills: [{"id": "broadsword", "points": 4, "specialty": "", "notes": ""}, ...]
    skills = models.JSONField(default=list, blank=True)
    spells = models.JSONField(default=list, blank=True)

    # Equipamento estruturado por categoria
    equipment_melee = models.JSONField(default=list, blank=True)
    equipment_ranged = models.JSONField(default=list, blank=True)
    equipment_armor = models.JSONField(default=list, blank=True)
    equipment_misc = models.JSONField(default=list, blank=True)

    # Maneuvers (cards): cada categoria é uma lista de manobras.
    # Melee/Ranged: {name, damage, nh, details}; Defense: {name, nh, details}.
    maneuvers_melee = models.JSONField(default=list, blank=True)
    maneuvers_ranged = models.JSONField(default=list, blank=True)
    maneuvers_defense = models.JSONField(default=list, blank=True)

    # Pontos: {"available": 150, "spent": 142, "breakdown": {"attributes": 50, "advantages": 30, "disadvantages": -20, "skills": 40, "secondary": 0}}
    points = models.JSONField(default=dict, blank=True)

    # Estado dinâmico em jogo (HP/FP atuais etc.) — mesmo padrão de V1
    runtime_stats = models.JSONField(default=dict, blank=True)

    # Flag pro GM marcar NPC rápido (mesmo conceito do V1)
    is_quick_npc = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["campanha", "nome_personagem"],
                name="unique_sheet_name_per_campanha_v2",
            )
        ]

    def __str__(self):
        return self.nome_personagem or f"Ficha V2 #{self.pk}"

    def save(self, *args, **kwargs):
        # Recalcula points.spent antes de salvar; secundárias derivadas são
        # computadas on-demand pelas views, não armazenadas.
        try:
            from gurps.sheet_v2_calc import recompute_points
            self.points = recompute_points(self)
        except Exception:
            # Em migrations e fixtures sem catálogo carregado, só mantém o que já está
            pass
        super().save(*args, **kwargs)


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


class SaveState(models.Model):
    campanha = models.ForeignKey(
        Campanha,
        on_delete=models.CASCADE,
        related_name="saves",
        blank=True,
        null=True,
    )

    data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Save de {self.user.username} para {self.campanha.nome}"
