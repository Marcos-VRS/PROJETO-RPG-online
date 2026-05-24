# Tabletop Map System — Plano técnico

> **Objetivo:** transformar a "imagem de fundo" atual da tela de jogo em um **mapa tabletop interativo** estilo Foundry/Roll20, mas enxuto e GURPS-first.
> **Status:** planejamento. Não há código escrito ainda.
> **Sessão de origem:** 2026-05-24 (user pediu antes de sair, retoma em ~1h).

---

## 1. RESUMO EM 5 LINHAS

1. O **asset atual** (`CampanhaAssets.image`) vira **Mapa**: imagem + grid hexagonal opcional + tokens + desenhos.
2. **GM troca o mapa rápido** (1 clique a partir de uma lista).
3. **Todos os usuários** podem desenhar (linhas, círculos, quadrados); **só o GM** move tokens de outros players.
4. **Tudo é WebSocket** — mudança aparece em real-time pra todos na campanha.
5. **Grid hexagonal flat-top** com 1 hex = 1 metro (mesma escala do GURPS yard, mas exibido em SI por convenção do projeto — ver `UNIT_CONVERSIONS.md`).

---

## 2. REQUISITOS DO USER (capturados literalmente)

> - "A imagem que é carregada na tela de jogo na verdade seja o Mapa/Banner"
> - "Simples e rápido trocar esses mapas"
> - "Mapas também devem ter um grid de batalha baseado em gurps, ou seja em hexágonos"
> - "Todos os usuários devem ser capazes de desenhar coisas simples no mapa, como linhas, círculos e quadrados"
> - "Sistema de token como se fosse um jogo de tabuleiro"
> - "Precisa ser visto em tempo real"
> - "Sistema de tabletop do site"
> - "Use as regras de GURPS como parâmetro"
> - "1 yard = 1 metro, lb → kg, etc"
> - "Em algum ponto vamos reconstruir a ficha para que atenda as regras de gurps a risca com o mapa"

---

## 3. ARQUITETURA

### 3.1 Modelo de dados

Modelo novo `MapState` (1:1 com `CampanhaAssets`):

```python
class MapState(models.Model):
    """Estado interativo de um mapa específico de uma campanha.

    Um CampanhaAssets é a IMAGEM + metadata; MapState é o que está em cima dela
    (tokens posicionados, desenhos, configuração de grid).
    """
    asset = models.OneToOneField(CampanhaAssets, on_delete=models.CASCADE, related_name='map_state')

    # Configuração do grid (definida pelo GM ao colocar o mapa)
    grid_enabled = models.BooleanField(default=True)
    grid_size_px = models.IntegerField(default=50)         # 1 hex = N pixels no display
    grid_offset_x = models.IntegerField(default=0)         # alinhamento fino
    grid_offset_y = models.IntegerField(default=0)
    grid_color = models.CharField(max_length=20, default='#000000')
    grid_opacity = models.FloatField(default=0.4)

    # Tokens posicionados (lista de dicts em JSON, mais simples que tabela separada)
    # Schema do token: ver §3.2 abaixo.
    tokens = models.JSONField(default=list, blank=True)

    # Desenhos (linhas, círculos, quadrados); ver §3.3.
    drawings = models.JSONField(default=list, blank=True)

    # Versão pra optimistic concurrency control.
    version = models.IntegerField(default=1)

    updated_at = models.DateTimeField(auto_now=True)
```

**Por que JSONField pra tokens/drawings e não tabela?**
- Quantidade pequena (≤100 tokens, ≤200 drawings por mapa).
- Sempre lê/escreve o blob inteiro (broadcast WS).
- Já temos infra de scene_state JSON; padrão consistente.
- Se virar pesado, fácil de migrar pra tabela depois.

### 3.2 Schema do Token

```json
{
  "id": "tok_a3f1",                    // gerado client-side, UUID curto
  "character_id": 1030,                // FK opcional pra CharacterSheetV2 (null = NPC sem ficha)
  "label": "Hector Santiago",          // override; senão usa nome_personagem
  "image_url": "/media/...",           // override; senão usa avatar do char ou ?
  "color": "#c9a55c",                  // borda + label

  "hex_x": 5,                          // coordenadas axiais do hex (q, r)
  "hex_y": 3,
  "facing": 0,                         // 0-5, lado do hex apontado (0 = leste)
  "size_modifier": 0,                  // SM do char (-1 a +4) → quantos hexes ocupa

  "posture": "standing",               // standing | crouching | kneeling | sitting | lying

  "status_effects": ["aiming"],        // lista de chaves; UI desenha ícones
  "hp_pct": 100,                       // só pra render (sync de runtime_stats)
  "fp_pct": 100,
  "hp_is_negative": false,

  "visible_to": "all",                 // all | gm_only | players (controle de fog of war)
  "z_index": 1                         // ordem de desenho (tokens grandes embaixo)
}
```

**Coordenadas hex axiais:** padrão flat-top de Red Blob Games (https://www.redblobgames.com/grids/hexagons/). Q = coluna, R = linha; cada hex tem (Q,R) único.

### 3.3 Schema do Drawing

```json
{
  "id": "drw_b7e2",
  "author_id": 42,                     // RegisterUser que desenhou
  "author_color": "#3b82f6",           // cor automática por usuário
  "kind": "line",                      // line | rect | circle | polygon
  "points": [[100, 200], [300, 400]],  // [[x1,y1],...] em pixels do mapa
  "stroke_color": "#ff0000",
  "stroke_width": 3,
  "fill_color": null,                  // opcional
  "label": null,                       // texto opcional ao lado
  "created_at": "2026-05-24T18:00:00Z",
  "ephemeral": false                   // true = some sozinho após 30s
}
```

**Cores automáticas por usuário:** já temos `Message.color` lógica similar; reaproveitar.

### 3.4 WebSocket Protocol

Reusa o canal `chat_<campanha_id>` que já existe. Novos message types:

**Cliente → Server:**

```json
// Mover token (GM ou owner do char)
{"type": "map_token_move", "asset_id": 1, "token_id": "tok_a3f1", "hex_x": 6, "hex_y": 3, "facing": 1}

// Criar token (GM only)
{"type": "map_token_add", "asset_id": 1, "token": {...}}

// Remover token (GM only)
{"type": "map_token_remove", "asset_id": 1, "token_id": "tok_a3f1"}

// Update token state (postura, status, label) — GM ou owner
{"type": "map_token_update", "asset_id": 1, "token_id": "tok_a3f1", "patch": {"posture": "crouching"}}

// Adicionar desenho (todos)
{"type": "map_drawing_add", "asset_id": 1, "drawing": {...}}

// Limpar desenhos (GM ou autor próprios)
{"type": "map_drawing_remove", "asset_id": 1, "drawing_id": "drw_b7e2"}

// Trocar mapa ativo da campanha (GM only)
{"type": "map_switch", "asset_id": 5}

// Configurar grid (GM only)
{"type": "map_grid_config", "asset_id": 1, "grid_size_px": 60, "grid_offset_x": 5, ...}
```

**Server → Cliente** (broadcast):

```json
// Estado completo do mapa após mudança
{"type": "map_state_changed", "asset_id": 1, "map_state": {...}}

// Apenas o token afetado (otimização pra moves frequentes)
{"type": "map_token_changed", "asset_id": 1, "token": {...}}
```

**Frequência de broadcasts:**
- Move de token: throttle 50ms client-side (broadcast a cada 50ms se arrastando).
- Desenho em curso: broadcast só no `mouseup` (não durante arrasto, pra economizar banda).
- Mudança discreta (postura, criar/remover): imediato.

### 3.5 Permissões

| Ação | GM | Owner do char | Outros players |
|---|---|---|---|
| Trocar mapa ativo | ✅ | ❌ | ❌ |
| Configurar grid | ✅ | ❌ | ❌ |
| Adicionar token | ✅ | ❌ | ❌ |
| Remover token | ✅ | ❌ | ❌ |
| Mover SEU token | ✅ | ✅ | ❌ |
| Mover token de OUTRO | ✅ | ❌ | ❌ |
| Trocar postura/status do SEU token | ✅ | ✅ | ❌ |
| Desenhar | ✅ | ✅ | ✅ |
| Apagar SEU desenho | ✅ | ✅ | ✅ |
| Apagar desenho de OUTRO | ✅ | ❌ | ❌ |

Backend valida cada `map_*` action checando `request.user` vs `character.owner` ou `campanha.dono`.

### 3.6 Stack de frontend

**Canvas HTML5 com 3 camadas sobrepostas:**

1. **Layer base** (`<img>`): imagem do mapa.
2. **Layer grid** (`<canvas>`): hexágonos desenhados em cima.
3. **Layer interativa** (`<canvas>`): tokens + drawings + cursor.

Não usar SVG: pode pesar com muitos tokens. Canvas tem render mais previsível.

Biblioteca? Pondero:
- **PixiJS** — fast WebGL, popular em Foundry. ~500KB.
- **Konva.js** — Canvas 2D com objetos arrastáveis, eventos. ~200KB. **Recomendada.**
- **Manual Canvas 2D** — zero deps, mas precisa reinventar hit-testing, drag-and-drop, layers.

**Decisão preliminar (pendente confirmação do user): Konva.js.**

Hex math: usar funções do Red Blob Games (axial coords, pixel→hex, etc.), copiadas inline. ~50 linhas de código.

---

## 4. FASES DE IMPLEMENTAÇÃO

### Fase 1 — Fundação (sem grid, sem tokens)
- Migration: `MapState` model + relação OneToOne com `CampanhaAssets`.
- UI: já tem `image-container` no `interface_jogo.html`; refatorar pra Canvas overlay.
- WS: `map_switch` (GM troca mapa).
- Sem grid, sem token, sem desenho ainda — só "imagem com pan/zoom".
- **Entrega:** GM consegue trocar mapas; player vê em tempo real; pan/zoom funcional.

### Fase 2 — Grid hexagonal
- Layer 2 (canvas grid): renderizar hex flat-top no tamanho configurado.
- UI do GM: input "tamanho do hex em pixels" + "offset X/Y" + "ligar/desligar grid".
- Broadcast `map_grid_config`.
- **Entrega:** GM ajusta grid no mapa; alinha com a arte de fundo.

### Fase 3 — Tokens
- Criar token a partir de uma ficha existente ("Adicionar à cena").
- Render do token no hex correspondente, com avatar.
- Drag-and-drop: GM move qualquer; owner move o próprio.
- Indicador de facing (seta na borda).
- Status visuals: pequenos ícones (postura, stunned, etc.).
- Sync HP/FP do token com `runtime_stats` em tempo real.
- **Entrega:** mapa tabletop básico funcional.

### Fase 4 — Desenhos
- Toolbar: linha / retângulo / círculo / cor / espessura.
- Click+drag desenha; cada desenho persistido.
- Apagar próprio desenho (right-click → delete).
- GM pode apagar qualquer.
- **Entrega:** colaboração visual funcionando.

### Fase 5 — Polimentos
- Régua: mede distância entre 2 hexes (em metros).
- Highlight de Reach quando seleciona token.
- Highlight do hex onde o cursor está.
- Atalhos de teclado (1-5 pra postura, F pra mudar facing).
- Fog of war (visibility por token).
- **Entrega:** UX completo.

### Fase 6 — Refatoração da Ficha pra alinhar com mapa
- Ficha V3 (?) que tenha Reach explícito por arma, range, área de efeito.
- Helper unit conversion centralizado.
- Token reflete state da ficha automaticamente.

---

## 5. INTEGRAÇÃO COM O QUE JÁ EXISTE

| Sistema atual | Como o mapa se conecta |
|---|---|
| `CampanhaAssets` | Vira "tipo de mapa". Adicionar campos `kind` (map/banner/handout) e `default_grid_size`. |
| `Campanha.scene_state` | Cenas continuam controlando **quem está em cena** (turn order). Cada cena agora também aponta pra um `active_map_id`. |
| `CharacterSheetV2.runtime_stats` | HP/FP de cada token vem daqui em tempo real (já temos sync). |
| Players-bar (minis topo) | Permanece. Token no mapa = mini na barra com mais detalhe espacial. |
| Side nav (atributos, perícias, ataques) | Permanece. Quando clica "Atacar" e tem token selecionado, o sistema sugere alvo (token mais próximo no Reach). |
| WS consumer `ChatConsumer` | Adicionar handlers `map_*`. Mesma infra, sem novo socket. |

---

## 6. DECISÕES CRAVADAS PELO USER (2026-05-24)

### Críticas (afetam arquitetura)

1. **Biblioteca de canvas:** ❌ Konva.js. ✅ **Canvas 2D puro**. Zero deps. Assistente reimplementa drag-and-drop, layers, hit-testing. Mais código mas controle total.

2. **Snap ao hex:** ✅ **Snap híbrido com Shift segurado**. Default: token sempre cola no centro do hex (Q,R) ao soltar. Segurando **Shift** durante o drag, movimento fica livre (pode parar entre hexes). Visual mostra os dois modos.

3. **Permissões de tokens:** ✅ **Só no próprio turno**. Token bloqueado fora do turno. GM pode destravar manualmente quando precisar (modo "edição livre"). Pra cenas sem combate (sem turn-bar ativa), tratar como modo livre por padrão.

4. **Hex orientation:** ✅ **Flat-top**. Lado plano em cima. Padrão GURPS oficial.

5. **Persistência de desenhos:** ✅ **Atrelados ao mapa, persistem**. Cada desenho fica no `MapState.drawings` do mapa específico. Trocar pra outro mapa esconde; voltar reaparece.

### Médias

6. **Régua de distância:** ✅ **Ambos** — botão na toolbar + shortcut R (sempre ativa). Cobre novatos e power users.

7. **Quem sobe imagens:** ✅ **Só GM**. Players sobem assets só via Journal (handouts pessoais).

8. **Quick NPCs no mapa:** ✅ **Mesmo fluxo atual** (CharacterSheetV2 com `is_quick_npc=True`). Reusa infra existente.

9. **Limite de mapas:** ✅ **Ilimitado**. Confiamos no OneDrive (~1MB/mapa).

### Baixas

10. **Cor de desenho:** ✅ **Auto por usuário + override**. Hash do username vira cor default; user pode trocar quando desenhar.

11. **Ícones de status:** ✅ **Conjunto estendido (12+) + GM Tool Box** (ver §6.1).

### 6.1 — GM TOOL BOX (decisão estrutural nova, 2026-05-24)

User pediu uma **biblioteca pessoal do GM** que persiste através de campanhas. Quando user é GM de qualquer campanha, ele acessa sua tool box e usa rapidamente o que já criou.

**O que vai na Tool Box:**
- **Status effects custom** (criados pelo GM ou copiados do livro)
- **Tokens reutilizáveis** (NPCs padrão tipo "goblin", "esqueleto", "guarda real")
- **Mapas favoritos** (futuro)
- **Drawings salvos** como templates (futuro)

**Modelo de dados:**

```python
class UserAsset(models.Model):
    """Biblioteca pessoal do user — reutilizável em qualquer campanha que ele
    é dono. Não vinculado a Campanha específica.
    """
    owner = models.ForeignKey(RegisterUser, on_delete=models.CASCADE, related_name='tool_box')
    kind = models.CharField(max_length=20, choices=[
        ('status_effect', 'Status Effect'),
        ('token', 'Token reutilizável'),
        ('map', 'Mapa template'),
        ('drawing', 'Desenho template'),
    ])
    name = models.CharField(max_length=80)
    data = models.JSONField()  # schema varia por kind
    image = models.ImageField(upload_to='user_assets/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, default='custom', choices=[
        ('custom', 'Criado pelo user'),
        ('book', 'Importado do livro'),
        ('preset', 'Preset do sistema'),
    ])
```

**Schema do `data` por kind:**

```json
// status_effect
{
  "icon": "💫" ou "/media/user_assets/myicon.png",
  "color": "#ff0000",
  "description": "Stunned: só Do Nothing, defesas -4",
  "mechanical_effect": {
    "modifies_attribute": "defense",
    "modifier": -4
  }
}

// token (NPC reutilizável)
{
  "character_data": {...},  // mesma estrutura mínima de CharacterSheetV2 (atributos + HP/FP)
  "default_size_modifier": 0,
  "default_image_url": "..."
}
```

**Onde aparece a UI:**
- Side nav do GM ganha **🧰 TOOL BOX** ícone.
- Modal mostra abas: Status / Tokens / Mapas / Desenhos.
- Cada item tem botão "Usar nesta campanha" → adiciona ao mapa atual.
- "Criar novo": form simples (nome, emoji/upload, descrição, efeito).
- "Importar do livro": picker dos `combat_tables.json` (statuses oficiais GURPS).

**Status effects iniciais (presets do sistema):**

12+ presets criados na primeira execução (migration data) — `source='preset'`:

| Status | Trigger | Efeito |
|---|---|---|
| Stunned | Major wound fail | Defesas -4, só Do Nothing |
| Knocked down | Major wound fail by 5+ | Lying down forçado |
| Unconscious | HP ≤ 0 + HT fail | Sem ações |
| Bleeding | cut/imp/pi com penetração | HT/min, perde 1 HP |
| Aiming | Aim maneuver | +Acc acumulado |
| Crippled (arm) | Dano > HP/2 em braço | Braço inutilizado |
| Crippled (leg) | Dano > HP/2 em perna | Move ½ |
| Grappled | Grapple | DX/skills -4 |
| Concentrating | Concentrate maneuver | Magia em prep |
| Major wound | Dano ≥ HP/2 num hit | Trigger HT roll |
| Hostile | Reação muito ruim | Aviso visual ao GM |
| Posture: Crouching | Change Posture | -2 melee atk/def |

**Onde aparecem visualmente:**
- ❌ NÃO no canto do token no mapa.
- ✅ **Abaixo das barras HP/FP do mini na players-bar superior**.
- Ícones pequenos (12px) em linha; até 5 por mini, resto vira "+N" tooltip.
- Sincronizados com `runtime_stats.status_effects` da ficha (não com o token no mapa) — atravessa mapas.

**Permissões:**
- Tool box é **por user**. Cada user só vê/edita a própria.
- Mas qualquer um pode aplicar um status ao próprio token (o GM aplica em qualquer).
- Player tem tool box vazia por default (não cria status). Pode ganhar feature de "favoritos" depois.

### Médias (afetam UX)

6. **Régua de distância:** ferramenta separada (clica no botão "régua", arrasta) ou sempre ativa (hover mostra distância do token selecionado)? **Sugestão: ferramenta separada (botão na toolbar), mas com modo "sempre ativo" via shortcut R.**

7. **Tokens de NPCs criados pelo GM (sem ficha completa)** — mesma flow do "quick character" atual? Sim/não?

8. **Limite de mapas por campanha:** quantos? Hoje `CampanhaAssets` é ilimitado. Quer manter, ou limitar (ex: 20)? **Sugestão: manter ilimitado; cada mapa tem ~1MB em média.**

9. **Quem cria mapas:** só GM, ou players também podem subir imagem? **Sugestão: só GM.** Players sobem assets via Journal.

### Baixas (afetam visual)

10. **Cor do desenho de cada user:** auto-atribuída (hash do username) ou escolha? **Sugestão: auto com override opcional.**

11. **Ícones de status:** quais os 6-8 mais importantes pra render no canto do token? Lista candidata: Aiming, Stunned, Crippled, Bleeding, Unconscious, Aiming, Grappled, KO.

---

## 7. RISCOS TÉCNICOS

| Risco | Mitigação |
|---|---|
| **Banda do Cloudflare Quick Tunnel** com many tokens movendo | Throttle 50ms; broadcast diff em vez de estado inteiro |
| **Imagens grandes (>5MB) lentas em sync** | Limit em upload (3MB max); converter pra webp no save |
| **Drift de coordenadas** quando GM e player têm zoom diferente | Coords sempre em "espaço do mapa" (pixels da imagem original); zoom é só transformação CSS |
| **Race condition em token moves** simultâneos | Optimistic: cliente assume vitória, server resolve com last-write-wins e re-broadcast |
| **Multi-mapa em uma cena** (ex: dungeon + visão tática) | Pra v1: 1 mapa ativo por cena. Múltiplos = roadmap futuro |

---

## 8. ARQUIVOS QUE VÃO MUDAR

```
gurps/
├── models.py                    # +MapState (OneToOne com CampanhaAssets)
├── consumers.py                 # +handlers map_token_*, map_drawing_*, map_switch
├── migrations/00XX_mapstate.py  # nova migration
├── units.py                     # NOVO — helper de conversões
└── views/interface_jogo.py      # adicionar map_state ao context

base_static/global/
├── js/
│   └── map/                     # NOVO diretório
│       ├── canvas.js            # Konva setup, layers
│       ├── hex.js               # math de hex flat-top (axial coords)
│       ├── tokens.js            # render + drag de tokens
│       ├── drawings.js          # toolbar + desenho
│       └── sync.js              # WS handlers do mapa
└── css/
    └── map.css                  # toolbar, cursor, etc.

base_templates/global/
└── interface_jogo.html          # substituir .image-container por <div id="map-root"></div>

docs/
├── TABLETOP_MAP_PLAN.md         # ESTE arquivo
├── GURPS_TABLETOP_RULES.md      # regras GURPS aplicáveis
└── UNIT_CONVERSIONS.md          # conversões pt-BR
```

Estimativa total: ~2000 linhas de JS novo, ~500 de Python, ~300 de CSS.

---

## 9. PRÓXIMOS PASSOS IMEDIATOS

Quando o user voltar:

1. Mostrar este doc + `GURPS_TABLETOP_RULES.md` + `UNIT_CONVERSIONS.md`.
2. Responder às **Perguntas Críticas (1-5)** acima — sem isso não dá pra avançar.
3. Confirmar a ordem das Fases (atualmente: fundação → grid → tokens → desenhos → polimento).
4. Decidir se faço a Fase 1 completa antes de qualquer outra coisa, ou parto direto pra Fase 3 (tokens) usando a infra atual de `CampanhaAssets`.

---

## 10. MEMÓRIA ASSOCIADA

Salvar memória `project-tabletop-architecture.md` quando começar a implementar:
- Decisões arquiteturais (canvas lib, hex orientation, snap)
- Schema do MapState
- Throttle de broadcast
- Permissões por papel

E referenciar daqui via `[[name]]`.
