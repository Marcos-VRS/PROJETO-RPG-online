# Tabletop — Fases 5 e 6 (planejamento de implementação)

> **Pré-requisito:** Fases 1-4 implementadas (canvas, grid, tokens, desenhos) + pendências da players-bar resolvidas (cor do dono, status effects).
> **Este doc:** blueprint detalhado pra implementar Fase 5 (Polimentos) e Fase 6 (GM Tool Box). Decisões arquiteturais já tomadas; serve de guia passo a passo.

---

## FASE 5 — Polimentos de combate

Foco: dar ao GM/players ferramentas visuais que reduzem fricção em combate GURPS. Tudo client-side sobre o canvas existente (sem mudança de modelo de dados, exceto onde indicado).

### 5.1 — Régua de distância

**O quê:** medir distância entre 2 pontos do mapa em hexes e metros (1 hex = 1m).

**Decisões (já cravadas):** ambos — botão na toolbar (`📏`) + shortcut `R`.

**Implementação:**
- Novo módulo `base_static/global/js/map/ruler.js` → `RulerLayer` registrado como overlay layer (mesmo composite de tokens/drawings).
- Estado: `mode` (none/measuring), `start` (world coords), `end`.
- Mousedown no modo régua marca `start`; mousemove atualiza `end`; mouseup mantém a medição visível até Esc ou novo clique.
- Render: linha tracejada `start→end` + label no meio mostrando `N hex · N m`.
- Distância em hex: `rd6Hex.distance(q1,r1,q2,r2)` após `pixelToAxial` de ambos os pontos. Multiplicar por 1 (1 hex = 1 m).
- Shortcut `R` alterna o modo. Botão `📏` na toolbar do mapa (adicionar à janela MAPA ou criar uma toolbar flutuante de ferramentas do mapa).
- **Não persiste** (efêmero, local-only — não precisa WS).

### 5.2 — Highlight de Reach ao selecionar token

**O quê:** quando um token está selecionado e tem um Reach (arma equipada), destacar os hexes alcançáveis.

**Implementação:**
- O token precisa saber o reach. Hoje o token não carrega reach. Opções:
  - (a) v1 simples: highlight fixo de Reach 1 (hexes adjacentes) ao selecionar qualquer token.
  - (b) v2: token carrega `reach: [1]` ou `[1,2]` puxado da arma equipada da ficha. Precisa adicionar `reach` ao schema do token em `_add_token` (lendo `equipped_weapons` ou `maneuvers_melee` da ficha).
- Render: hexes alcançáveis com tint verde-claro translúcido. Usar `rd6Hex.neighbor` em anéis.
- Função `hexRing(center, radius)` em hex.js (a criar): retorna todos os hexes a distância exata `radius`.
- **v1 = Reach 1 fixo** (rápido). v2 lê da ficha (depois).

### 5.3 — Movement preview ao arrastar token

**O quê:** ao arrastar um token, mostrar trajetória + custo em hex + limite de Basic Move.

**Implementação:**
- Já temos drag no tokens.js. Adicionar no `mousemove` do drag:
  - Desenhar linha pontilhada do hex original ao hex atual.
  - Label com `N hex / M m`.
  - Se `N > basic_move` do char → linha vermelha (excedeu movimento).
- Token precisa carregar `basic_move`. Adicionar ao schema do token (puxar de `sub_attributes.basic_move` da ficha em `_add_token`).
- Render no overlay durante o drag (já há `_dragging` state).

### 5.4 — Highlight do hex sob o cursor

**O quê:** feedback visual de qual hex o mouse está sobre.

**Implementação:**
- `mousemove` no overlay (quando não arrastando) → calcula hex sob cursor → desenha contorno destacado.
- Throttle via requestAnimationFrame.
- Simples, melhora muito a usabilidade.

### 5.5 — Atalhos de teclado consolidados

Já temos: `+`/`-` (tamanho), `1`/`2`/`3` (camada), `Delete` (remover), `R` (régua, a fazer).
Adicionar:
- `F` / `Shift+F`: girar facing horário/anti-horário (já tem botão ↻ na toolbar).
- `Esc`: desseleciona token / cancela régua / cancela modo desenho.

### Ordem de implementação da Fase 5
1. Highlight do hex sob cursor (5.4) — base, mais fácil.
2. Régua (5.1) — usa o hex highlight.
3. Movement preview (5.3) — token precisa de basic_move no schema.
4. Highlight de reach v1 (5.2) — Reach 1 fixo.
5. Atalhos consolidados (5.5).

---

## FASE 6 — GM Tool Box (UserAsset)

Foco: biblioteca pessoal do GM, persistente entre campanhas. Pedido explícito do user (2026-05-24). Esboço original em `TABLETOP_MAP_PLAN.md §6.1`.

### 6.1 — Modelo de dados

```python
class UserAsset(models.Model):
    """Biblioteca pessoal do user (GM), reutilizável em qualquer campanha
    onde ele é dono. NÃO vinculado a campanha específica."""
    owner = models.ForeignKey(RegisterUser, on_delete=models.CASCADE,
                              related_name='tool_box')
    kind = models.CharField(max_length=20, choices=[
        ('status_effect', 'Status Effect'),
        ('token', 'Token reutilizável'),
        ('map', 'Mapa template'),
        ('drawing', 'Desenho template'),
    ])
    name = models.CharField(max_length=80)
    data = models.JSONField(default=dict)   # schema varia por kind
    image = models.ImageField(upload_to='user_assets/', blank=True, null=True)
    source = models.CharField(max_length=20, default='custom', choices=[
        ('custom', 'Criado pelo user'),
        ('book', 'Importado do livro'),
        ('preset', 'Preset do sistema'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
```

Migration: criar model. Migration data: criar os 18 status presets (de `status_icons.js`) — mas como `source='preset'` eles são compartilhados, NÃO por-user. Decisão: presets são read-only globais (não no UserAsset); UserAsset só guarda CUSTOM e BOOK do GM. Os presets vêm de `status_icons.js` (front) — não precisam estar no DB.

**Revisão:** UserAsset guarda só o que o GM cria/importa. Presets ficam no `status_icons.js` (já existe). Simplifica.

### 6.2 — Schema do `data` por kind

```json
// status_effect (custom)
{ "icon": "emoji ou /media/user_assets/x.png", "color": "#ff0000",
  "description": "...", "mechanical_note": "defesas -4" }

// token (NPC reutilizável)
{ "label": "Goblin", "size_modifier": 0, "size_scale": 1.0,
  "color": "#3b82f6", "default_layer": "visible",
  "stat_block": { "st":10, "dx":11, ... } }   // opcional
```

### 6.3 — Endpoints (REST, não WS — é CRUD pessoal)

```
GET    /toolbox/                       lista do user logado (JSON ou página)
POST   /toolbox/create/                cria (kind, name, data, image)
POST   /toolbox/<id>/delete/           remove (só owner)
POST   /toolbox/<id>/use/<campanha>/   aplica na campanha atual:
                                       - token → cria token no mapa ativo
                                       - status → aplica ao char selecionado
```

### 6.4 — UI

- Side nav GM ganha ícone **🧰 TOOLBOX**.
- Modal com abas: Status / Tokens / Mapas / Desenhos.
- Cada item: nome, ícone/preview, botões "Usar" e "Excluir".
- "Criar novo": form (nome, emoji ou upload, descrição, cor).
- "Importar do livro": picker dos status oficiais GURPS (de `combat_tables.json`) → cria UserAsset `source='book'`.
- Aplicar status a um token/char: integra com a mini (botão de status no token selecionado → escolhe da toolbox).

### 6.5 — Aplicar status a um personagem

- Novo WS handler `character_status_set`: `{char_id, status_effects: [...]}`.
- Valida GM (via token auth já implementado).
- Atualiza `runtime_stats.status_effects` da ficha (V1/V2).
- Broadcast `character_updated` → minis re-renderizam status (já temos o pipeline).
- UI: token selecionado → botão 🏷 na toolbar → dropdown de status (presets + toolbox do GM) → toggle.

### Ordem de implementação da Fase 6
1. Model UserAsset + migration + admin.
2. Endpoints CRUD básicos.
3. WS `character_status_set` + aplicar status (reusa status_icons.js no front).
4. UI Toolbox modal (status primeiro, tokens depois).
5. "Importar do livro" (status oficiais).
6. Tokens reutilizáveis (criar token a partir de UserAsset).

---

## DEPENDÊNCIAS E RISCOS

| Item | Depende de | Risco |
|---|---|---|
| Movement preview | token carregar basic_move | baixo (adicionar campo no _add_token) |
| Reach highlight v2 | token carregar reach da arma | médio (ler equipped_weapons da ficha) |
| Aplicar status | WS character_status_set + pipeline character_updated | baixo (pipeline já existe) |
| Toolbox tokens | UserAsset.data com stat_block | médio (decidir quanto da ficha copiar) |

## O QUE NÃO ENTRA (v2/v3)

- LOS automático, cover automático (continuam manuais).
- Magia automatizada.
- IA de NPC.
- Ficha V3 (roadmap separado em FICHA_V3_ROADMAP.md).
