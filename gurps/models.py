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

    # Contexto acumulado pra geração por IA: cresce a cada item aprovado (imagem
    # ou mapa). Alimenta os prompts junto com descricao/regras/journal pra manter
    # coerência de mundo/estilo entre as artes. Ver gurps/ai_context.py.
    ai_context = models.TextField(blank=True, default="")

    # Configuracao do grid hexagonal. GLOBAL por campanha — todos os mapas
    # compartilham a mesma config. Ao trocar mapa, grid nao reseta.
    grid_enabled = models.BooleanField(default=False)
    grid_size_px = models.IntegerField(default=50)
    grid_offset_x = models.IntegerField(default=0)
    grid_offset_y = models.IntegerField(default=0)
    grid_color = models.CharField(max_length=20, default="#000000")
    grid_opacity = models.FloatField(default=0.4)

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


class MapState(models.Model):
    """Estado interativo de um CampanhaAssets que está sendo usado como mapa.

    Um CampanhaAssets é a imagem + metadata; MapState carrega o que é interativo
    em cima dela (config do grid, tokens posicionados, desenhos). Cada asset
    pode ter zero ou um MapState — auto-criado na primeira vez que uma
    campanha abre aquele asset na tela de jogo.

    Detalhes do plano em docs/TABLETOP_MAP_PLAN.md.
    """
    asset = models.OneToOneField(
        CampanhaAssets,
        on_delete=models.CASCADE,
        related_name="map_state",
    )

    # Configuração do grid hexagonal (flat-top, 1 hex = 1 metro)
    grid_enabled = models.BooleanField(default=False)
    grid_size_px = models.IntegerField(default=50)         # raio do hex em px
    grid_offset_x = models.IntegerField(default=0)         # alinhamento fino
    grid_offset_y = models.IntegerField(default=0)
    grid_color = models.CharField(max_length=20, default="#000000")
    grid_opacity = models.FloatField(default=0.4)

    # Tokens posicionados. Schema do token em docs/TABLETOP_MAP_PLAN.md §3.2.
    tokens = models.JSONField(default=list, blank=True)

    # Desenhos colaborativos. Schema em §3.3.
    drawings = models.JSONField(default=list, blank=True)

    # Versão pra optimistic concurrency. Incrementa a cada save.
    version = models.IntegerField(default=1)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MapState do asset #{self.asset_id}"


class UserAsset(models.Model):
    """Biblioteca pessoal do user (tipicamente GM), reutilizável em QUALQUER
    campanha onde ele é dono. NÃO vinculado a campanha específica.

    Guarda status effects custom, tokens reutilizáveis (NPCs padrão), etc.
    Os presets de status do sistema NÃO ficam aqui — vivem em
    `status_icons.js` (front). UserAsset é só o que o GM cria/importa.

    Detalhes em docs/TABLETOP_NEXT_PHASES.md §6.
    """
    KIND_CHOICES = [
        ("status_effect", "Status Effect"),
        ("token", "Token reutilizável"),
        ("map", "Mapa template"),
        ("drawing", "Desenho template"),
    ]
    SOURCE_CHOICES = [
        ("custom", "Criado pelo user"),
        ("book", "Importado do livro"),
        ("preset", "Preset do sistema"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tool_box",
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    name = models.CharField(max_length=80)
    # Schema do data varia por kind. Ver docs.
    data = models.JSONField(default=dict, blank=True)
    image = models.ImageField(upload_to="user_assets/", blank=True, null=True)
    source = models.CharField(max_length=20, default="custom", choices=SOURCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["kind", "name"]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.name} ({self.owner_id})"


class GenWorkerStatus(models.Model):
    """Heartbeat do worker de geração de mapas (Claude headless).

    Linha única (singleton, pk=1). O worker atualiza ``last_seen`` a cada tick;
    o endpoint de pedido usa isso pra saber se o gerador está online. Sem
    heartbeat recente = gerador offline (degradação graciosa — nunca quebra).
    """
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Gen worker status"

    @classmethod
    def is_online(cls, threshold_seconds: int = 45) -> bool:
        row = cls.objects.filter(pk=1).first()
        if not row or not row.last_seen:
            return False
        return (timezone.now() - row.last_seen).total_seconds() < threshold_seconds

    @classmethod
    def beat(cls) -> None:
        cls.objects.update_or_create(pk=1, defaults={"last_seen": timezone.now()})

    def __str__(self):
        return f"worker last_seen={self.last_seen}"


class MapGenRequest(models.Model):
    """Pedido de geração de mapa por IA (fila).

    O GM manda um prompt → cria-se um pedido ``pending`` que NUNCA depende do
    gerador estar de pé (o serviço não quebra). O worker (Fase 3) pega os
    pending, gera o SVG e marca ``done``. O GM aprova/descarta (Fase 4).
    """
    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("processing", "Processando"),
        ("done", "Pronto (aguardando aprovação)"),
        ("failed", "Falhou"),
        ("approved", "Aprovado"),
        ("discarded", "Descartado"),
    ]
    campanha = models.ForeignKey(
        Campanha, on_delete=models.CASCADE, related_name="mapgen_requests"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    prompt = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    grid_size_px = models.IntegerField(default=64)  # snapshot da escala no pedido
    result_svg = models.TextField(blank=True, default="")  # SVG gerado (Fase 3)
    result_asset = models.ForeignKey(
        CampanhaAssets, on_delete=models.SET_NULL, null=True, blank=True
    )  # asset criado após aprovação (Fase 4)
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"MapGen #{self.id} [{self.status}] {self.prompt[:40]}"


class ImageGenRequest(models.Model):
    """Pedido de geração de imagem por IA local (ComfyUI na GPU do host).

    Serve pra TUDO — retratos de personagem e mapas. O worker `imagegen_worker`
    pega os pending, chama o ComfyUI, salva o PNG e marca ``done``. O GM aprova
    (vira CampanhaAssets show=False) ou descarta. Nunca depende do ComfyUI estar
    de pé (offline = erro amigável, não quebra o serviço).
    """
    KIND_CHOICES = [
        ("personagem", "Personagem"),
        ("mapa", "Mapa"),
        ("cena", "Cena"),
        ("capa", "Capa / título"),
        ("item", "Item / objeto"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("processing", "Processando"),
        ("done", "Pronto (aguardando aprovação)"),
        ("failed", "Falhou"),
        ("approved", "Aprovado"),
        ("discarded", "Descartado"),
    ]
    campanha = models.ForeignKey(
        Campanha, on_delete=models.CASCADE, related_name="imagegen_requests"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default="personagem")
    prompt = models.TextField()
    negative = models.TextField(blank=True, default="")
    width = models.IntegerField(default=768)
    height = models.IntegerField(default=1024)
    steps = models.IntegerField(default=6)
    cfg = models.FloatField(default=1.6)
    seed = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    result_file = models.CharField(max_length=300, blank=True, default="")  # rel. ao MEDIA_ROOT
    result_asset = models.ForeignKey(
        CampanhaAssets, on_delete=models.SET_NULL, null=True, blank=True
    )
    error = models.TextField(blank=True, default="")
    # Imagem de referência opcional (IP-Adapter): transfere o estilo/clima dela
    # pra geração. Ex.: mandar a arte "ESDRAS" e gerar outro personagem com a
    # mesma vibe. ref_weight controla a força (0=ignora, 1=força total).
    ref_image = models.ImageField(upload_to="imagegen_refs/", blank=True, null=True)
    ref_weight = models.FloatField(default=0.7)
    # Referência escolhida do próprio journal (alternativa ao upload). O worker usa
    # a imagem desse asset no IP-Adapter se ref_image não vier.
    ref_asset = models.ForeignKey(
        CampanhaAssets, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
    )
    # Estilo escolhido na UI (chave do seletor) + se deve ler o journal (contexto).
    style = models.CharField(max_length=32, blank=True, default="cinematic_dark")
    use_context = models.BooleanField(default=True)
    # Título a escrever POR CIMA da imagem (modo capa). O modelo de IA não escreve
    # texto legível, então o nome do episódio é sobreposto via Pillow.
    title = models.CharField(max_length=200, blank=True, default="")
    # Prompt final que o claude escreveu a partir do journal (pra o GM ver/depurar).
    expanded_prompt = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ImageGen #{self.id} [{self.status}/{self.kind}] {self.prompt[:40]}"


class VideoGenRequest(models.Model):
    """Pedido de geração de VÍDEO por IA local (AnimateDiff na GPU do host).

    Monta um vídeo anime longo (~90s+) por MONTAGEM: o claude lê o journal e
    escreve um storyboard (várias tomadas), o worker gera cada tomada como um
    clipe curto (AnimateDiff), o ffmpeg costura tudo + trilha por clima. Mesmo
    padrão de fila/aprovação do ImageGenRequest; nunca quebra o serviço.
    """
    STATUS_CHOICES = [
        ("editing", "Editando beats"),
        ("pending", "Pendente"),
        ("processing", "Processando"),
        ("done", "Pronto (aguardando aprovação)"),
        ("failed", "Falhou"),
        ("approved", "Aprovado"),
        ("discarded", "Descartado"),
    ]
    # "auto" = storyboard automático (o claude escreve tudo; fluxo antigo).
    # "beats" = editor de beats (o GM dita cena por cena na timeline do áudio).
    MODE_CHOICES = [("auto", "Storyboard automático"), ("beats", "Editor de beats")]
    campanha = models.ForeignKey(
        Campanha, on_delete=models.CASCADE, related_name="videogen_requests"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    mode = models.CharField(max_length=8, choices=MODE_CHOICES, default="auto")
    # Duração do áudio escolhido (minutagem base pra alinhar os beats na timeline).
    audio_duration_ms = models.IntegerField(default=0)
    prompt = models.TextField()  # pedido cru do GM
    style = models.CharField(max_length=32, blank=True, default="anime")
    use_context = models.BooleanField(default=True)
    target_seconds = models.IntegerField(default=90)  # duração alvo do vídeo final
    width = models.IntegerField(default=512)
    height = models.IntegerField(default=512)
    fps = models.IntegerField(default=8)
    steps = models.IntegerField(default=8)
    cfg = models.FloatField(default=1.8)
    mood = models.CharField(max_length=32, blank=True, default="")  # pra trilha
    # Música escolhida pelo GM (rel. ao MEDIA_ROOT, ex. "music/epic/x.mp3").
    # Vazio = escolha automática pelo clima.
    music_file = models.CharField(max_length=300, blank=True, default="")
    # Storyboard que o claude escreveu: [{"prompt": "...", "seconds": 4}, ...]
    storyboard = models.JSONField(blank=True, null=True, default=list)
    expanded_prompt = models.TextField(blank=True, default="")  # storyboard legível
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    progress = models.CharField(max_length=120, blank=True, default="")  # "tomada 3/20"
    # GM pediu pra pausar: o worker para após a cena atual e monta o parcial.
    pause_requested = models.BooleanField(default=False)
    result_file = models.CharField(max_length=300, blank=True, default="")  # rel. ao MEDIA_ROOT
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"VideoGen #{self.id} [{self.status}] {self.prompt[:40]}"


class VideoBeat(models.Model):
    """Um BEAT (cena) de um projeto de vídeo em modo editor.

    O GM dita cena por cena na timeline do áudio. Cada beat tem um prompt
    (cumulativo: o claude lê os beats anteriores pra manter coerência), uma
    imagem de referência opcional do journal, uma duração (fatia do áudio) e um
    clipe gerado. Beat longo = vários clipes de 2s encadeados (Modo Consistência).
    Transição controla como ele entra em relação ao beat anterior na montagem.
    """
    STATUS_CHOICES = [
        ("empty", "Sem clipe (não gerado)"),
        ("pending", "Na fila"),
        ("processing", "Gerando"),
        ("done", "Pronto"),
        ("failed", "Falhou"),
    ]
    TRANSITION_CHOICES = [("cut", "Corte seco"), ("crossfade", "Crossfade")]

    project = models.ForeignKey(
        VideoGenRequest, on_delete=models.CASCADE, related_name="beats"
    )
    order = models.IntegerField(default=0)  # sequência (derivada de start_ms)
    # O beat é um TRECHO da música: de start_ms até end_ms (timestamps). A
    # montagem usa a ordem cronológica. duration_ms = end-start (mantido em sync
    # pela view; é o que decide o tamanho do clipe/quantos sub-clipes de 2s).
    start_ms = models.IntegerField(default=0)
    end_ms = models.IntegerField(default=2000)
    duration_ms = models.IntegerField(default=2000)  # = end_ms - start_ms
    user_prompt = models.TextField(blank=True, default="")  # o que o GM ditou
    correction = models.TextField(blank=True, default="")  # instrução de correção p/ regerar
    expanded_prompt = models.TextField(blank=True, default="")  # prompt cumulativo (claude)
    ref_asset = models.ForeignKey(
        CampanhaAssets, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
    )
    seed = models.BigIntegerField(null=True, blank=True)  # base; sub-clipes = seed+i
    clip_file = models.CharField(max_length=300, blank=True, default="")  # rel. ao MEDIA_ROOT
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="empty")
    progress = models.CharField(max_length=120, blank=True, default="")
    error = models.TextField(blank=True, default="")
    # Transição DESTE beat em relação ao anterior (o 1º beat ignora).
    transition = models.CharField(max_length=10, choices=TRANSITION_CHOICES, default="cut")
    transition_ms = models.IntegerField(default=500)  # duração do crossfade
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Beat #{self.id} (proj {self.project_id}) ord={self.order} [{self.status}]"
