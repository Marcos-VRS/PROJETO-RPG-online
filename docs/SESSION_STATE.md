# Session State — onde parei e como continuar

> **Última sessão:** 2026-05-24 (planejamento do tabletop).
> **Status:** planejamento detalhado do sistema de mapa/tabletop documentado em 5 docs. Próximo passo: aguardar respostas do user às perguntas críticas e começar Fase 1 (fundação do canvas).
>
> Quando voltar, leia este documento primeiro.

---

## SESSÃO 2026-05-24: Planejamento do Tabletop Map System

**Contexto:** sessão de produção rodou OK no fim de semana (players migraram fichas pra V2). User pediu pra começar a planejar o sistema de **mapa tabletop interativo** com:
- Grid hexagonal (1 hex = 1 metro)
- Tokens estilo jogo de tabuleiro
- Desenhos colaborativos (linhas, círculos, quadrados) em tempo real
- Base nas regras GURPS 4e
- Unidades pt-BR (yard→m, lb→kg, etc.)

Pediu pra eu **ler todas as regras de GURPS** e documentar antes de mexer em código. Sem perturbar — voltaria em 1h. Esta sessão é só docs.

**Documentos criados (4 novos):**

1. **`docs/TABLETOP_MAP_PLAN.md`** — plano técnico completo:
   - Modelo de dados `MapState` (OneToOne com `CampanhaAssets`)
   - Schema do Token (hex coords, facing, posture, status, image, color)
   - Schema do Drawing (kind, points, stroke, ephemeral)
   - WebSocket protocol (`map_token_move/add/remove/update`, `map_drawing_*`, `map_switch`, `map_grid_config`)
   - Stack: Canvas HTML5 + 3 layers (imagem, grid, interativo) + **Konva.js** (recomendado)
   - 6 Fases de implementação (fundação → grid → tokens → desenhos → polimentos → ficha V3)
   - **11 perguntas pro user** (5 críticas, 4 médias, 2 baixas)

2. **`docs/GURPS_TABLETOP_RULES.md`** — regras GURPS aplicáveis:
   - Conversões pt-BR (yard=m, lb→kg)
   - Hex flat-top, SM → hexes ocupados
   - Facing (front/side/back), Reach
   - Ordem de turnos, 13 manobras principais
   - Postura (5 estados)
   - Fluxo ataque/defesa/dano
   - Status effects (8 tipos) com triggers

3. **`docs/UNIT_CONVERSIONS.md`** — sistema de unidades:
   - **Regra de ouro: 1 yard = 1 metro** (simplificação intencional do user)
   - Tabela completa de conversões
   - Helpers Python (`gurps/units.py` a criar) e JS (`base_static/.../units.js`)
   - Política: JSONs do catálogo mantêm imperial; conversão só na exibição

4. **`docs/TABLETOP_COMBAT_FLOW.md`** — fluxo passo a passo de combate no mapa:
   - Setup (GM coloca tokens, sistema ordena por Speed)
   - Turno individual (manobra → move/step → action → defesa → dano)
   - 13 manobras com move/defesa permitido
   - 12 status effects com ícones propostos
   - Régua, highlight de Reach, movement preview
   - 9 atalhos de teclado propostos
   - Casos especiais GURPS (reach multi-hex, close combat, mounted)

5. **`docs/FICHA_V3_ROADMAP.md`** — placeholder pra Ficha V3:
   - User antecipou: "em algum ponto vamos reconstruir a ficha para que atenda as regras de gurps a risca com o mapa"
   - Schema preliminar (equipped_weapons estruturado, runtime com aim_accumulated, etc.)
   - V3 só DEPOIS de tabletop estar funcional e validado
   - Migração V2→V3 lateral, mesma pattern V1↔V2

**Decisões propostas (aguardando confirmação):**
- Hex flat-top
- Konva.js como lib de canvas
- Snap automático ao centro do hex
- Player só pode mover token no próprio turno
- Desenhos atrelados ao mapa específico (não somem)
- Cor de desenho auto-atribuída por usuário
- v1 sem LOS automático nem cover automático (manual)

**Perguntas críticas a fazer:**
Ver `TABLETOP_MAP_PLAN.md` §6 — 11 perguntas numeradas.

**Próximo passo concreto:**
Quando user voltar, mostrar os 5 docs e perguntar as 5 perguntas críticas. Depois disso começar Fase 1 (substituir `.image-container` por canvas Konva, manter funcional sem grid/token).

---

## SESSÃO 2026-05-16 (NOITE): UX da tela de jogo + sync em tempo real + bugfixes estruturais

**Player side nav (coluna vertical esquerda):**
- Substitui o menu inferior antigo (`.personagem-container` oculta via CSS).
- Ícones: 💪 ATR · 🛠 SKL · ⚔ ATK · 🛡 DEF · 🥋 EQP · 🎲 D6 · ＋ EDIT · 📋 FICHA · 📖 JRNL · 🚪 SAIR.
- Nome do personagem ativo em `top: 118px` (acima da nav).
- Botão `→` (próximo personagem) fora do aside, ao lado direito; só aparece com 2+ fichas. Rotaciona via `?character=<id>`.
- Nav escorrega scroll se ícones excederem altura (`overflow-y: auto`).

**GM side nav:** mesma estrutura, 4 ícones: D6, GM (Fichas), JRNL, SAIR. FICHA/GM e JOURNAL abrem em nova aba.

**Chat:** `.coluna-chat` e `.chat-container` em `top: 116px` — encosta na turn-bar (que vai até ~114px). Sem mais gap no topo após remoção do menu antigo.

**Quickedit (criar/remover cards no jogo):**
- Botão `+ EDIT` abre `#janela-quickedit` com 3 botões (Melee/Ranged/Defesa) + form inline Nome+Dano+NH.
- Endpoints: `POST /v2/api/Ficha/<id>/quickadd/<kind>/` e `.../quickremove/<kind>/<index>/`.
- Suporta V1 (`nome/detalhes`) e V2 (`name/details`) — `_resolve_sheet_any` detecta tipo.

**Vitals editor (GM ajusta HP/FP):**
- Click num mini abre popover anchored com -5/-1/+1/+5 e input direto.
- HP pode ir negativo (até -10×hp_max), FP min 0.
- Endpoint `POST /character/<id>/vitals/` (V1 e V2). Broadcast `character_vitals_changed`.

**HP negativo (barra "morte"):**
- HP < 0 → classe `.is-negative` na `.player-mini-bar-hp`. Barra degradê roxo (`#6d28d9 → #a855f7`).
- `_hp_pct_and_negative(hp, max)` em `interface_jogo.py:231`.

**Click fora fecha modal:** listener mousedown em `game_interface.js`.

**Sync em tempo real (save em outra aba reflete no jogo SEM refresh manual):**
- `_broadcast_character_updated()` em `sheet_v2.py:30+` é chamado após `sheet.save()` no editar_v2.
- WS event `character_updated` → frontend atualiza mini (HP/FP/nome/avatar). Se a ficha é a ativa do user, dispara `rd6PartialRefreshJanelas`: fetch silencioso da page + DOM-swap das janelas modais. Throttle 1.5s.
- Consumer handler em `gurps/consumers.py:151`.

**Bugs corrigidos:**
1. **IDs V1↔V2 colidiam** (V1.id=4 e V2.id=4 simultâneos). Migration `0059_v2_id_offset.py` avança `sqlite_sequence` da V2 pra `max(max(V1.id), max(V2.id)) + 1000`. Próximos V2 nascem em IDs ~1030+.
2. **Turno marcava 2 minis ao mesmo tempo** (consequência do #1): `rd6CharById` e `rd6ApplySceneStateToBar` agora fazem coerção `Number(...)`.
3. **Turno mostrava "—"**: consumer normaliza `current_turn_id` pra int (`gurps/consumers.py:88+`). Cai pro primeiro da lista se inválido.
4. **chat.js:47 TypeError** ao clicar Próximo: chat.js processava broadcasts não-chat. Guard `typeof data.message !== 'string' return`.
5. **Menu modal abaixo da side-nav**: z-index duplicado em `.menu-modal-backdrop` (1800+200) e `.menu-modal` (1900+201). Remove os antigos, fica só 1800/1900. **Lição registrada:** evitar adicionar declaração sem remover a antiga no mesmo seletor.
6. **CSS edits em base_static/ não apareciam em desktop dev**: Whitenoise serve do `STATIC_ROOT` quando coletado. Solução: rodar `collectstatic --noinput` após cada edit. Memória `feedback-collectstatic-desktop.md` registrada.
7. **Template HTML cacheado em desktop dev**: Django usa `cached.Loader` automaticamente em `DEBUG=False`. `project/settings.py:120+` agora condiciona pra `sys.frozen` (só ativa em bundleado).

**Admin Django:** `CharacterSheetV2` registrado em `gurps/admin.py:218+` com JSONEditorWidget. Aparece como "Character sheet v2s".

**Outros:**
- Editor V2 com preview imediato de foto (`URL.createObjectURL`).
- Botão "Criar nova ficha" letras pretas (`#000 !important`).
- Menu carregar campanha: título absolute no topo + botões centralizados.

---

## SESSÃO 2026-05-16: Catalogação GURPS + Ficha V2 (sessão diurna anterior)

### Catálogos GURPS (todos em `gurps/data/*.json`, todos com prefixo `name_en` priorizado)

| Arquivo | Conteúdo | Status |
|---|---|---|
| `attributes.json` | ST/DX/IQ/HT + secundárias + damage table + encumbrance | ✅ completo |
| `advantages.json` | **246 vantagens** (Basic Set cap 2 + Powers cap 2) | ✅ full detail |
| `disadvantages.json` | **179 desvantagens** (Basic Set cap 3) | ✅ full detail |
| `modifiers.json` | **100 modifiers** (57 enhancements + 43 limitations + 3 gadget) | ✅ full detail |
| `skills.json` | **236 perícias curadas** com defaults | ✅ full detail (recurada manualmente — versão regex tinha lixo) |
| `spells.json` | 63 spells por colégio | metadata only |
| `equipment.json` | 67 items core (melee/ranged/armor/shields) + cost of living | ✅ |
| `templates.json` | meta-traits + character + racial templates | samples |
| `combat_tables.json` | 20 maneuvers + 11 damage types + 11 hit locations + defesas | ✅ |
| `diseases_poisons.json` | 12 diseases + 12 poisons + 12 hazards | ✅ |
| `bestiary.json` | 20 animais/monstros stat blocks | samples |
| `technology.json` | 13 TLs + 20 artifacts | samples |
| `sample_powers.json` | 40 sample powers do livro Powers cap 3 | ✅ |
| `reference_tables.json` | Reaction Table, Size/Speed/Range, Fright Check, etc. | ✅ |

**Helper de cálculos:** `gurps/sheet_v2_calc.py` — `compute_secondary(primary, mods)`, `cost_advantage_entry`, `flatten_advantages_for_picker`, `flatten_disadvantages_for_picker`, `flatten_skills_for_picker`, `flatten_modifiers_for_picker`. Todos usados no JS frontend e no model save.

### Ficha V2 (`CharacterSheetV2`) — migration 0058

Modelo novo lado a lado com `CharacterSheet` (V1, legado). **NUNCA destrua V1** (regra inviolável: fichas antigas precisam migrar intactas).

- FK real para `Campanha` + `RegisterUser` (vs strings dentro de JSON em V1)
- Campos JSON: `primary_attributes`, `secondary_modifiers`, `advantages`, `disadvantages`, `skills`, `equipment_melee/ranged/armor/misc`, `maneuvers_melee/ranged/defense`, `runtime_stats`, `points`
- `is_quick_npc` BooleanField (igual flag V1)
- Auto-recalcula `points` no `save()` via `recompute_points`
- `unique_together` = (`campanha`, `nome_personagem`)

### UI Editor V2 (`base_templates/global/sheet_v2/editar_ficha_v2.html` + `editor.js`)

- Single-page com seções: Identidade · Atributos · Secundárias (auto-calc) · Advantages · Disadvantages · Skills · Equipment · Maneuvers Attack/Defense
- **Picker dropdown** com autocomplete pra Advantages/Disadvantages/Skills/Modifiers (lê do catálogo via `/v2/api/catalog/<kind>/`)
- **Variantes do catálogo** (cost.choices) viram entradas separadas no dropdown com subtítulo entre parênteses
- **Modo manual** (toggle 📖↔✏) — pode escrever vantagem livre + custo manual
- **Botão MOD** em cada advantage/disadvantage abre drawer com Enhancements/Limitations (mesmo picker, percent fica ali)
- **MOD em Skills** — coluna pra +/-N somado direto no NH final
- **Maneuvers Cards** (estilo legado) com nome/damage/NH/details
- **Auto-cálculo em tempo real** (JS): HP/FP/Will/Per/Speed/Move/Dodge/BL/Thrust/Swing/custo total
- **NH de skill**: 1pt=base, 2-3pt=+1, 4-7pt=+2, 8-11pt=+3, depois +4pt cada +1 (corrigido em 2026-05-16)
- **Cache-Control no-store** na response do editor pra evitar cache de navegador
- **Save feedback**: barra verde "✓ salva" / vermelha com erro específico no topo

### Fase 2: V1→V2 no resto do site

`gurps/views/interface_jogo.py` agora usa wrapper `_wrap_v2_as_legacy(v2)` que adiciona aliases:
- `atributos.ST/DX/IQ/HT` (em CAPS, como template legado lê)
- `sub_attributes.hp/fp/will/perception/dodge/basic_lift/parry_unarmed/etc.` (calculadas via `compute_secondary`)
- `skills[].nome` (=label), `.nh` (=computed_level)
- `maneuvers_*[].nome` (=name), `.detalhes` (=details)
- `equipment_*[].nome` (=name)
- `advantages[].nome` (=label), `.custo` (=computed_cost)
- `info_campanha` construído de owner/campanha/is_quick_npc

Helpers: `_get_player_sheets_v2_then_v1(campanha, username)`, `_get_all_sheets_for_campanha(campanha)`.

Views/templates atualizados pra usar V2 (com fallback V1 quando V2 não existe):
- `carregar_fichas` (menu Fichas) → lista V2 do user; Legado em seção colapsada
- `lista_carregar_ficha.html` → links pra editar_v2
- `lista_campanhas_nova_campanha.html` → criar_v2 (depois de criar campanha)
- `interface_jogo.html` botão FICHA (player) → direto pra `lista_v2_player`
- `editar_fichas_menu` + `menu_fichas_gm` → V2 primário, Legado em `<details>` colapsável
- `interface_jogo.py game_interface` → V2 (com wrapper) ou V1 fallback
- `_resolve_avatar_url`, `_serialize_char_for_client`, `get_character_gm`, `journal` → V2 + V1
- `save_quick_character` → cria V2 (não V1!)
- `delete_quick_character` → procura V2 primeiro

### Pendências (próxima sessão)

- **Reescrita "nativa" do template `interface_jogo.html`** pra V2 (sem aliases) — opcional, futuro
- **Player picker funciona via input `id` digitado** — adicionar autocomplete também nos modais da tela de jogo
- **Quirks list** (Characters p162-165): traits de -1pt; ainda não no catálogo
- **Skills/Spells expansion**: muitas estão como `list_only`, precisam descrições completas pra autocomplete rico
- **WebSocket consumer**: scene_state ainda usa IDs V1/V2 misturados — pode dar bugs em edge cases
- **Migrator V1→V2** opcional pra players preencherem rápido a partir da legado (decidimos NÃO fazer e player redigita)

---

## SESSÕES ANTERIORES (resumo)

---

## Pivô estrutural de 2026-05-14

O produto deixou de ser SaaS hospedado no GCP e virou **aplicativo desktop com dois cliques** (Windows). Detalhes em [`AGENT_PROMPT.md`](AGENT_PROMPT.md) e [`DESKTOP_DISTRIBUTION.md`](DESKTOP_DISTRIBUTION.md). Resumo das decisões:

| Decisão | Escolha |
|---|---|
| Banco do produto | SQLite (`%APPDATA%\roll3d6\data.sqlite3`) |
| Multiplayer | Cloudflare Quick Tunnel (URL rotária por sessão) |
| Channel layer | InMemoryChannelLayer (sem Redis) |
| Empacotamento | PyInstaller `--onedir --noconsole` + Inno Setup |
| UI do launcher | pywebview (HTML/CSS embutido) |
| Destino do SaaS GCP | Sunset gradual (congelado, desligado quando desktop maduro) |
| Assinatura de código | Adiada (SmartScreen na 1ª execução é aceito) |
| RAG | **Hibernado** — código preservado, comentado em INSTALLED_APPS e urls.py |

---

## Estado das fases

| Fase | Descrição | Status |
|---|---|---|
| 0 | Reset de documentação | ✅ concluída |
| 1 | venv Windows + Django/SQLite local funcionando | ✅ concluída, validada visualmente |
| 2 | Launcher (daphne + cloudflared + UI pywebview) | ✅ concluída, validada |
| 3 | Empacotamento PyInstaller (`dist\roll3d6\roll3d6.exe`) | ✅ concluída |
| 3.5 | Inno Setup → `roll3d6-setup.exe` | ✅ concluída + ícone dos 3 dados |
| 3.6 | OneDrive sync + lock file (`session.lock`) | ✅ concluída |
| 3.7 | Commits do trabalho (4 commits limpos em `main`) | ✅ concluída |
| 3.8 | Fix `/media/` em desktop mode (commit `e013ed6`) | ✅ concluída |
| 4 | Migração de dados GCP Postgres → SQLite desktop | ✅ concluída |
| 4.5 | Deletar bucket descartável `gs://onyx-antler-452215-k1-tmp` | 🟡 pendente (comando preparado, falta usuário rodar) |
| **R1** | **Design system v1 (tokens, partial, paleta Foundry, Inter/Cinzel)** | ✅ commit `e0bf872` |
| **R2** | **Game interface redesign (players-bar + scene + turn + chat + quick char)** | ✅ commit `51791b4` |
| **R3** | **Aplica skin em todas as telas (login/lista/journal/criar/editar/etc)** | ✅ commit `c305189` |
| 5 | Sunset GCP (banner + export + desligar VM) | ⏳ não começado (sem prazo) |
| 6 | Polimento visual pós-feedback do usuário | 🟡 próxima sessão |

---

## O que existe no repo hoje (uncommitted)

**Modificados:**
- `CLAUDE.md` — índice atualizado para o pivô desktop
- `requirements.txt` — removido `channels_redis`/`redis`, adicionado `pywebview`. Em UTF-8 sem BOM (era UTF-16 antes — armadilha que travou o pip).
- `project/settings.py` — múltiplas adições condicionais ao modo desktop (ver "Mudanças principais em settings.py" abaixo)
- `project/urls.py` — `rag.urls` comentado
- `docs/AGENT_PROMPT.md` — reescrito
- `docs/RAG_ARCHITECTURE.md` — prefixado com nota de hibernação
- `docs/SESSION_STATE.md` — este arquivo
- `.gitignore` — adicionada exceção `!desktop/roll3d6.spec` + `/build/` + `warn-*.txt` + `xref-*.html`

**Novos:**
- `docs/DESKTOP_DISTRIBUTION.md` — arquitetura completa do instalador
- `desktop/` — pacote do launcher (ver árvore abaixo)
- `static/` — gerado por `collectstatic`, **gitignored**
- `db.sqlite3` na raiz — banco do dev em modo `python manage.py runserver`, **gitignored**
- `%APPDATA%\roll3d6\` (FORA do repo) — banco do modo desktop com:
  - `data.sqlite3` (admin user: `admin` / senha `admin`)
  - `secret.key` — chave Django
  - `bin\cloudflared.exe` (~50 MB, baixado uma vez)
  - `logs\daphne.log`, `logs\cloudflared.log`

**Bundle pronto:**
- `dist\roll3d6\roll3d6.exe` — 18 MB, com pasta `_internal` de ~114 MB. Total ~132 MB. **Gitignored**, gerar com `desktop\build.ps1`.

### Árvore de `desktop/`

```
desktop/
├── __init__.py
├── launcher.py            # entry point: orquestra setup_django + server + tunnel + ui
├── runtime_config.py      # %APPDATA%\roll3d6, SECRET_KEY auto-gerada
├── server.py              # spawn de daphne (subprocess) — frozen-aware
├── tunnel.py              # cloudflared: bundle-first, fallback download
├── ui.py                  # janelinha pywebview com HTML+JS inline
├── roll3d6.spec           # PyInstaller spec (com django.setup() no header)
├── build.ps1              # collectstatic + pyinstaller num comando só
├── _smoketest.py          # teste manual: config + porta + download cloudflared
└── _e2e_test.py           # teste manual: pipeline E2E headless (sem UI)
```

Os arquivos `_smoketest.py` e `_e2e_test.py` são utilitários de debug — podem ser mantidos ou removidos, não rodam automaticamente.

---

## Mudanças principais em `project/settings.py`

Tudo controlado por **uma única env var**: `ROLL3D6_DESKTOP_HOME`. Quando setada (sempre que o launcher inicia), ativa o modo desktop.

```python
DESKTOP_HOME = Path(os.environ.get("ROLL3D6_DESKTOP_HOME") or "") or None
```

Comportamento condicional:

| Setting | Modo dev (sem var) | Modo desktop dev (var setada, não-frozen) | Modo bundleado (var + frozen) |
|---|---|---|---|
| `SECRET_KEY` | hardcoded | de `%APPDATA%\roll3d6\secret.key` | idem |
| `DEBUG` | True | False | False |
| `ALLOWED_HOSTS` | lista fixa | `["*"]` | `["*"]` |
| `DATABASES.default.NAME` | `BASE_DIR/db.sqlite3` | `%APPDATA%\roll3d6\data.sqlite3` | idem |
| `MEDIA_ROOT` | `BASE_DIR/media` | `%APPDATA%\roll3d6\media` | idem |
| `CHANNEL_LAYERS` | InMemory (default) | InMemory | InMemory |
| `STATICFILES_STORAGE` | manifest | `StaticFilesStorage`+`USE_FINDERS` | `CompressedStaticFilesStorage` |
| `STATIC_ROOT` | `BASE_DIR/static` | idem | `_MEIPASS/static` |
| `CSRF_TRUSTED_ORIGINS` | domínio prod | localhost + `ROLL3D6_TUNNEL_URL` se presente | idem |

Modo `gcp_legacy` (Redis): ativado por `ROLL3D6_MODE=gcp_legacy`. Não usado em dev/desktop.

---

## Como rodar / testar (cheat sheet)

```powershell
# Pré-requisito: estar em PROJETO-RPG-online com .venv ativada.
.\.venv\Scripts\Activate.ps1

# 1. Modo dev clássico (db.sqlite3 na raiz, DEBUG=True)
python manage.py runserver

# 2. Modo desktop em dev (não-bundleado) — sobe launcher com UI
python -m desktop.launcher

# 3. Teste E2E headless (sem UI) do pipeline launcher
python -m desktop._e2e_test

# 4. Rebuild do .exe completo
.\desktop\build.ps1
# saída: dist\roll3d6\roll3d6.exe

# 5. Rodar o .exe bundleado
Start-Process dist\roll3d6\roll3d6.exe

# 6. Smoke test: bate em 19 URLs autenticadas, valida 200
python -m desktop._smoke_urls
```

---

## Estado da UI no fim desta sessão (2026-05-16)

**Game interface (tela de jogo):**
- Players-bar fixa no topo: minis com avatar + nome + barra HP vermelha + barra FP azul (25% maior).
- Toggle dark/light (☀/☾) e esconder avatares (👤). Botão ☰ (GM only) abre menu lateral.
- Turn controls bar abaixo: "Turno: <nome>" + ◀ Anterior / Próximo ▶ (GM only). Mini do turno atual com borda vermelha + glow. Rotação visual da fila ao avançar.
- Chat sidebar direita: opaco, 14.94% / mín 286px, 3 partes (header Sair/Journal/GM + lista + input 64px).
- Janelas internas (Dados/Atributos/etc) centradas, top 115px.
- Privacidade: GM vê HP/FP de todos; player só das fichas próprias.

**Scene control (menu lateral GM):**
- Multi-cena cap 10, pills + "+ Nova". Nome editável (Enter salva).
- Form "Nova ficha rápida" (nome + HP + FP + MOVE + asset opcional pra avatar).
- Busca, checkboxes pra cena, ordem inicial por Speed desc + ▲▼ reordena (= turno).
- 🗑 só em fichas quick (importadas do GCP ficam protegidas).
- Sync tempo real via WebSocket.

**Telas redesenhadas:** login, register, index, lista_campanhas, journal — refator completo.
**Demais telas:** cobertas pela camada "legacy skin overrides" em design_tokens.css (re-mapeia `--primary-color` etc. pros tokens v1 via !important).

**Tema:** default dark, toggle pra light (pergaminho). Persiste em localStorage('rd6-theme'), aplicado pre-CSS pra evitar flash.

**Dados:** `%OneDrive%\roll3d6\` (sync automático).
**Bundle:** `dist\roll3d6-setup.exe` (53.2 MB).

---

## Gotchas descobertos nesta sessão (não esquecer)

1. **PyInstaller + Django: `collect_submodules('gurps')` falha silenciosamente** se Django não está configurado quando o spec é avaliado. Sintoma: `App 'gurps' doesn't have a 'RegisterUser' model` no startup do bundle. **Fix:** o spec faz `django.setup()` no header antes de `collect_submodules`. **Plus** lista explícita de `gurps.*` como rede de segurança.
2. **`requirements.txt` UTF-16:** o arquivo veio de outra máquina em UTF-16-LE com BOM, pip parsava errado. Reescrito em UTF-8 puro. Se algum script futuro reescrever via PowerShell `Out-File`, **passar `-Encoding utf8`** ou usar `[System.IO.File]::WriteAllText` com `UTF8Encoding($false)`.
3. **Whitenoise + DEBUG=False sem collectstatic:** em modo dev-launcher (não-frozen), `WHITENOISE_USE_FINDERS=True` resolve. Em modo bundleado, precisa de `collectstatic` em **build-time** (o `build.ps1` cuida disso) e `STATIC_ROOT=_MEIPASS/static`.
4. **Sandbox do Claude Code não eleva UAC:** `Start-Process -Verb RunAs` falha silenciosa. Comandos que precisam de admin (WSL, certbot, etc.) o usuário tem que rodar manualmente.
5. **`*.spec` no .gitignore:** o template Python padrão ignora todos os `.spec`, mas precisamos do `desktop/roll3d6.spec` em commit. Adicionada exceção `!desktop/roll3d6.spec`.
6. **`daphne` subprocess no .exe frozen:** `sys.executable` aponta pro próprio `roll3d6.exe`. Subprocess passaria `--daphne` como flag — o `launcher.main()` detecta esse arg e executa `daphne.cli` em vez de abrir a UI de novo.
7. **`tar.exe` nativo do Windows corrompe nomes UTF-8:** ao extrair `.tar.gz` com nomes acentuados (Episódio, Guardião, etc.), arquivos ficam com mojibake (`Epis├│dio_01.jpg`) e o Django serve 404. **Fix:** usar `tarfile` do Python (que respeita UTF-8 nativo). Vale lembrar quando implementar import wizard (#21).
8. **GCP VM com OS Login ativo:** metadata SSH keys e arquivos `authorized_keys` são ignorados — auth força conta Google. Pra rodar `gcloud` com permissão de owner, fazer `gcloud auth login --no-launch-browser` na VM. Browser SSH funciona sempre.
9. **Browser SSH ⚙️ Download File** é uma flaky — popup pode fechar instantâneo sem erro visível, JSON abre inline em vez de baixar. Mais confiável: `gcloud storage cp` pra bucket descartável + download pelo Console UI.
10. **`/media/` em desktop mode com `DEBUG=False`:** Django não anexa rota automaticamente. Precisa de `django.views.static.serve` explícito em `urls.py` (commit `e013ed6`).
11. **Django `{# ... #}` é single-line!** Multi-linha vira texto puro renderizado. Qualquer `{% include %}` dentro de um pseudo-comentário multi-linha vira recursão infinita. Use `{% comment %} ... {% endcomment %}` pra multi-linha.
12. **CSS `backdrop-filter` cria containing block.** Aplicar `backdrop-filter`/`filter`/`transform` num ancestral faz com que `position: fixed` dos descendentes posicione relativo ao ancestral, não ao viewport. Janelas modais saem da tela. Use com cuidado.
13. **PyInstaller `--noreload` + edição de Python:** runserver com --noreload NÃO recarrega código Python (só templates). Sempre reiniciar o server após mudar views/consumers. Cache de templates Django também pode persistir em alguns cenários — `python manage.py runserver` fresh resolve.
14. **Daphne deve estar no TOPO de INSTALLED_APPS:** sem `'daphne'` antes de `django.contrib.staticfiles`, runserver inicia em WSGI puro e WebSockets retornam 404. No bundle .exe daphne roda como subprocess separado, mas em dev essa diretriz é obrigatória.

---

## Como ficou o fluxo de import (referência pro futuro — task #21)

Quando for hora de transformar isso num **fluxo automático no launcher** (botão "Importar backup" na UI):

1. UI pede um arquivo `.json` (Django dumpdata) e opcionalmente um `.tar.gz` (mídia).
2. Backup automático do `data.sqlite3` atual pra `data.sqlite3.bak_<timestamp>`.
3. `migrate` no banco atual (idempotente — só roda se faltar migration).
4. `loaddata <arquivo.json>` — usa `django.core.management.call_command`.
5. Extração do tar com **`tarfile` do Python** (não shell `tar.exe`, que corrompe UTF-8).
6. Mostra resumo (counts por model) e pergunta se manter ou reverter pro backup.

Esse fluxo escapa toda a dança do GCP que fizemos manualmente nesta sessão.

---

## Como retomar Fase 4 (HISTÓRICO — Fase 4 já concluída em 2026-05-15)

Mantido aqui caso precise refazer um import futuro do GCP enquanto a VM ainda existir.

### 1. Verificar primeiro se os arquivos já estão no PC

Antes de tudo, Claude deve checar:
```powershell
Get-ChildItem "$env:USERPROFILE\Downloads\roll3d6_*"
```
Se aparecer `roll3d6_dump.json` e `roll3d6_media.tar.gz` → pula direto pro item 4 (loaddata).
Se não aparecer → seguir 2 e 3.

### 2. Reabrir a VM no GCP Console e o Browser SSH

1. **console.cloud.google.com** → ☰ → **Compute Engine** → **VM instances**.
2. Se a VM `roll3d6rpgvm` estiver **Stopped** (provável, porque usuário desligou pra economizar): marca o checkbox dela → clica **▶ Start / Resume** → espera "Running" (~30s).
3. Anota o **External IP** atual (pode ter mudado).
4. Na linha da VM, clica em **SSH** (terceira coluna pela direita) → abre janelinha de Browser SSH.

### 3. Regenerar o dump (caso /tmp tenha sido limpo) e baixar

Cola este bloco no Browser SSH — primeiro confirma se os arquivos ainda existem; se não, refaz:

```bash
# Se /tmp ainda tem os arquivos da sessão anterior, pula direto pro download.
ls -lh /tmp/roll3d6_dump.json /tmp/roll3d6_media.tar.gz 2>&1

# Se NÃO encontrou, rode o script abaixo pra regenerar:
cd /home/marcosvrsdevmail/roll3d6rpgapp
for d in venv .venv env; do [ -f "$d/bin/activate" ] && source "$d/bin/activate" && break; done
python manage.py dumpdata \
  --natural-foreign --natural-primary --indent 2 \
  --exclude=contenttypes --exclude=auth.permission \
  --exclude=admin.logentry --exclude=sessions.session \
  --exclude=rag \
  > /tmp/roll3d6_dump.json && echo "dump OK"
[ -d media ] && tar czf /tmp/roll3d6_media.tar.gz media/ && echo "media OK"
ls -lh /tmp/roll3d6_dump.json /tmp/roll3d6_media.tar.gz
```

**Download (a parte que ficou pendente!):**

Na janela do Browser SSH, no canto **SUPERIOR DIREITO** tem ícone de **engrenagem (⚙️)**. Sequência:

1. Clica no ⚙️ → escolhe **"Download file"** no menu suspenso
2. Abre um campo de texto → digita `/tmp/roll3d6_dump.json` → clica **Download**
3. O browser baixa pro `Downloads\` (padrão do Chrome/Edge)
4. Repete pro segundo arquivo: ⚙️ → Download file → `/tmp/roll3d6_media.tar.gz` → Download

**Verificação:**
- Os 2 arquivos devem aparecer em `C:\Users\marco\Downloads\`
- `roll3d6_dump.json` ~ alguns MB (texto JSON)
- `roll3d6_media.tar.gz` ~ tamanho variável dependendo do volume de imagens

### 4. Importar no SQLite limpo de teste (Claude executa)

1. **Importar num SQLite limpo de teste primeiro** (não tocar no `%OneDrive%\roll3d6\data.sqlite3` ainda). Caminho sugerido: `%LOCALAPPDATA%\Temp\roll3d6_import_test\`.
2. Comandos esperados:
   ```powershell
   $env:ROLL3D6_DESKTOP_HOME = "$env:LOCALAPPDATA\Temp\roll3d6_import_test"
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py loaddata $env:USERPROFILE\Downloads\roll3d6_dump.json
   tar -xzf "$env:USERPROFILE\Downloads\roll3d6_media.tar.gz" -C "$env:ROLL3D6_DESKTOP_HOME"
   ```
3. Validar: subir runserver, abrir admin, conferir que usuários/fichas/campanhas vieram.
4. Se OK: ou faz o mesmo no `%OneDrive%\roll3d6\` real, ou implementa o fluxo "importar dados" na primeira execução do launcher (task #21).
5. Documentar o fluxo em `DESKTOP_DISTRIBUTION.md`.
6. Depois disso, **lembrar de pedir o usuário pra desligar a VM no Console** (economia GCP) já que a Fase 4 técnica estará concluída.

**Pontos de atenção previstos:**
- Conteúdo `contenttypes` foi excluído do dump — IDs no SQLite vão diferir do Postgres. Se algum modelo tem FK direta pra ContentType (raro), pode quebrar. Verificar.
- `AUTH_USER_MODEL = "gurps.RegisterUser"` precisa estar registrado antes do loaddata. O `migrate` garante isso.
- Senhas dos usuários antigos vêm hasheadas no dump — funcionam direto no SQLite (Django re-hidrata).
- Mídias com caminho absoluto da VM (`/home/marcosvrsdevmail/...`) precisam ser ajustadas pra `%OneDrive%\roll3d6\media\`. Verificar campos de imagem nos models e ajustar paths se necessário.

---

## Roadmap remanescente (depois da Fase 3.5)

### Fase 4 — Migração de dados GCP → desktop
- Script de export na VM: `python manage.py dumpdata --natural-foreign --natural-primary` filtrando por `gurps.*`.
- Copiar pasta `media/` da VM (avatars, mapas, fichas com upload).
- Fluxo de "primeira execução" no app desktop: opção "começar do zero" ou "importar dados exportados" (apontar para `.json` + pasta `media/`).
- Testar com dump real da produção.

### Fase 5 — Distribuição + sunset GCP
- Banner no site SaaS GCP avisando descontinuação + link do download.
- Botão de export por usuário no site SaaS (gera `.json` + zip de mídias do usuário).
- Acompanhar migrações.
- Após prazo (a definir): parar daphne na VM, desligar VM, liberar recursos GCP.

---

## Notas operacionais preservadas

- **GCP VM (`35.239.231.110`, banco `roll3d6_data_base`)** está congelada. Não evoluir, só patches críticos. SSH continua via chave cadastrada no metadata.
- **Chave OpenAI** no `~/.roll3d6_secrets` da VM GCP — não é usada hoje.
- **Banco de produção GCP** continua autoritativo até a migração da Fase 4.
- **Máquina local:** Windows 11 Pro, Python 3.13.7, GPU RTX 1000 Ada (não usada hoje, fica útil quando RAG voltar com SQLite-vss).
