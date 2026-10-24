# Geração de mapas por IA (Claude headless) — Plano técnico

> **Status:** planejamento aprovado (2026-08-09). Não começou a implementação.
> **Origem:** user quer que o GM envie um prompt no jogo → o PC host gera um mapa/planta na escala do tabletop → aparece no site pra todos, com fluxo de aprovação.

## Decisões cravadas (confirmadas pelo user 2026-08-09)

1. **Motor = Claude Code headless.** O Django dispara `claude -p "<prompt>"` como subprocesso **na máquina host** (o PC que roda o app + túnel). Usa a **mesma assinatura/tokens** da sessão interativa (SEM custo de API separado), e **não depende de terminal/chat aberto**. Requisito: `claude` CLI instalado e logado no host (já é o caso no PC do user).
   - Alternativas descartadas: (1) terminal interativo em `/loop` — depende de terminal aberto; (2) API Anthropic pura — conta/cobrança separada (API key, pague-por-uso).
2. **Formato do mapa = SVG vetorial.** Nítido em qualquer zoom, arquivo pequeno (bom pro limite de banda do túnel), editável. O canvas do tabletop carrega SVG como imagem. Gerado **na escala do tabletop** (1 hex ≈ 1 m; usa `Campanha.grid_size_px`).
3. **Destino = asset com `show` DESMARCADO, via aprovação.** A imagem gerada NÃO entra direto: fica **pendente no journal do GM**; só é persistida de vez se o GM clicar **"Aprovar"**. Aprovada → vira `CampanhaAssets` com `show=False`, disponível pro GM trabalhar (definir como fundo de cena etc.).
4. **Degradação graciosa (requisito inviolável):** se o gerador estiver indisponível (Claude offline no host) ou estourar timeout, a funcionalidade **dá erro amigável mas NÃO quebra** o jogo/chat/mapa. O endpoint de pedido nunca depende do gerador estar de pé.

## Arquitetura

```
GM (host OU remoto via túnel) → chat "🗺️ Gerar mapa"
   → POST /map-gen/request/  (Django cria MapGenRequest status=pending; responde na hora)
   → [fila no banco]  ←  heartbeat do worker
   → Worker no host (dispara `claude -p`) pega pending, gera SVG na escala, salva arquivo
   → marca done + broadcast WS → journal do GM mostra a imagem PENDENTE
   → GM aprova → vira CampanhaAssets(show=False) → some da lista de pendentes
```

- **"Banco da internet" = banco local do host.** Como todos leem via túnel, salvar no SQLite local já aparece pra todos. Nada de infra externa.

## Fases

### Fase 1 — Reforma da tela de Assets/Journal (fundação; começa primeiro)
- Journal vira **janela modal** na tela de jogo (não mais aba/página separada), com **z-index ACIMA do chat**.
- **Menu de filtro fixo** no topo da modal + lista filtrável.
- Miniaturas **menores**; clicar numa → abre a **imagem grande por cima da tela** (lightbox).
- **FIX do bug do `show`:** hoje `game_interface` (interface_jogo.py ~L405) filtra `show=True` pra todos, então o **GM não vê assets com show desmarcado** dentro do jogo. Corrigir: GM vê todos; players só `show=True`. (A view `journal` L1053 já mostra tudo pro GM, mas a tela de jogo não — inconsistência.)

### Fase 2 — Fila + degradação graciosa ✅ FEITO (2026-08-15)
- **Modelos** (migration 0063, aditiva): `MapGenRequest` (campanha, requested_by, prompt, status[pending/processing/done/failed/approved/discarded], grid_size_px snapshot, result_svg, result_asset FK, error, timestamps) + `GenWorkerStatus` (singleton pk=1, `last_seen`; `.beat()` / `.is_online(threshold=45s)`).
- **Endpoints** (`gurps/views/map_gen.py`): `POST /map-gen/<campanha_id>/request/` (GM only) cria pending e responde na hora com `worker_online`; `GET /map-gen/status/<req_id>/` faz poll com **timeout lazy** (pending/processing > 180s + offline → `failed`). Registrado no admin.
- Verificado end-to-end (offline cria pending, heartbeat→online, não-GM 403, prompt vazio 400, timeout→failed).
- **Falta:** UI (prompt input + "Gerando…"/poll) — decidido fazer junto da Fase 4 (aprovação); e o worker (Fase 3).

### Fase 3 — Motor headless ✅ FEITO (2026-08-15)
- Management command **`python manage.py mapgen_worker`** (`gurps/management/commands/mapgen_worker.py`). Loop: `GenWorkerStatus.beat()` → pega pending → `claude -p` → extrai `<svg>...</svg>` → salva em `result_svg`, status `done` (ou `failed`). `--once` processa 1 (teste); `--interval`/`--timeout`/`--claude` configuráveis.
- **Gotchas resolvidos (Windows):**
  - `claude` é `claude.CMD` (npm) → `subprocess` não acha via PATHEXT. **Fix:** `shutil.which()` resolve o caminho real.
  - Prompt multi-linha como arg do `.CMD` mangava → virava resposta conversacional. **Fix:** prompt via **stdin** (`communicate(input=...)`).
  - `claude` rodando na raiz lia o `CLAUDE.md` e virava "assistente do projeto". **Fix:** `cwd=tempfile.gettempdir()` (neutro).
  - Heartbeat fresco durante a geração (>45s): `communicate` numa thread + `beat()` na main loop.
- Verificado: gerou SVG válido 1098×1098 (~15KB) pra "sala de pedra com porta e fogueira". Requer `claude` CLI logado no host (mesma assinatura).
- **Falta:** rodar o worker junto do app (launcher/desktop) — hoje é comando manual; e escolher modelo/tuning de qualidade/velocidade.

### Fase 4 — UI + fluxo de aprovação ✅ FEITO (2026-08-15)
- **Onde:** caixa "🗺️ Gerar mapa (IA)" no menu ☰ do GM (não no journal — mais prático pra ferramenta de GM; o asset aprovado aparece no journal). Prompt textarea + "Gerar" → dispara pedido → status "Gerando…" → **poll** de `/map-gen/<camp>/list/` a cada 5s.
- **Pendentes/prontos** renderizados em cards: `done` mostra **preview** (`<img src=/map-gen/svg/<id>/>`, abre no lightbox) + **Aprovar** / **Descartar**; `failed` mostra o erro.
- **Endpoints** (map_gen.py): `GET /map-gen/<camp>/list/`, `GET /map-gen/svg/<id>/` (image/svg+xml), `POST /map-gen/<id>/approve/` (grava SVG em `media/campanhas_assets/gen_<id>.svg` + cria `CampanhaAssets(show=False, slot=2)` + status `approved`), `POST /map-gen/<id>/discard/`.
- Verificado end-to-end: aprovar #3 criou asset #117 (show=False), arquivo no disco, req approved, sai da lista; re-aprovar 400. UI: JS/CSS inline no template (sem collectstatic).
- **Falta pra usar de verdade:** rodar o `mapgen_worker` junto do app (hoje é comando manual — `python manage.py mapgen_worker`). No desktop, o launcher deve subir o worker ao lado do daphne.

## Pendências de decisão (futuras)
- Onde o prompt-input mora exatamente (chat principal vs box dedicado "🗺️ Gerar mapa").
- Como o worker é acionado (subprocesso on-demand pelo request vs mini-loop de poll). Provável: request enfileira; um tick leve dispara `claude -p`.
- Prompt-template de geração (iterar na qualidade do SVG).
