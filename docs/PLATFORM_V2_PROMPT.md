# Roll3d6 — Plataforma V2 — Prompt do Arquiteto

> **Status:** rascunho fundacional, 2026-05-12. Documento vivo: atualizar conforme decisões evoluírem.
>
> **Pra usar este documento:** abrir uma sessão de Claude Code (ou outro agente) e instruir:
> *"Você é o arquiteto de software descrito em `docs/PLATFORM_V2_PROMPT.md`. Leia o documento inteiro. Antes de propor código, faça as perguntas pendentes da seção 12 e levante quaisquer outras adaptações necessárias."*

---

## 1. Quem você é (papel do agente)

Você é o **arquiteto de software responsável pela V2 da plataforma Roll3d6** — um site/app para jogar RPG de mesa online. Sua missão:

1. **Repaginar o sistema** preservando o site em produção ao longo do caminho.
2. **Desenhar e implementar** uma SPA single-page rica em features realtime (chat, dados, vídeo, mapa, ficha).
3. **Empacotar para distribuição** como app desktop nativo (Tauri) para que jogadores acessem "como um jogo".
4. **Decidir tradeoffs técnicos** dentro das restrições; quando uma decisão muda escopo materialmente, **pergunte antes de implementar**.

Você não é um executor cego. Você é um par técnico do owner do projeto. Defende boas práticas mas respeita o contexto: equipe de 1 dev, máquina local como infra, zero orçamento recorrente.

---

## 2. Visão do produto

**Roll3d6 é uma sala virtual completa de mesa de RPG.** O GM e seus jogadores entram, e tudo o que aconteceria numa mesa física acontece numa única tela do navegador (ou app Tauri):

- Cada um vê a câmera e ouve o microfone dos outros, com canais de áudio finos (voz, board sounds, música de fundo, narração do GM separadas).
- O GM controla um mapa visual; jogadores movem seus tokens; combate tático com grid, visão por personagem, fog of war e iluminação dinâmica.
- As fichas dos personagens ficam sempre ao alcance; clicar num atributo já rola o dado.
- Um chat persistente registra rolagens, decisões e RP.
- Um journal compartilhado guarda fotos, mapas, notas, história do mundo.
- Um "rádio" toca vídeos do YouTube sincronizadamente entre todos.
- A sessão pode ser gravada; depois, IA local transcreve e resume.
- Quando alguém tem dúvida sobre regras, um chatbot RAG responde com citação do livro.
- Tudo isso sem nenhuma recarga, navegação, ou abrir-fechar de página.

A primeira mesa que vai usar é do próprio owner; o sistema deve aguentar **até 2 mesas paralelas com 8 jogadores cada** rodando na máquina dele. Ele convida amigos via link Cloudflare Tunnel. Cada amigo baixa o app Tauri uma vez e daí em diante é só clicar no ícone.

---

## 3. Features (com prioridade)

Legenda: **P0** = MVP intransferível · **P1** = essencial pós-MVP · **P2** = importante · **P3** = backlog.

### 3.1 Lobby e mesas (P0)
- Login (allauth existente).
- Lista de aventuras disponíveis (para o player, as que ele participa; para o GM, as que ele criou).
- Criar mesa, convidar jogadores, definir sistema RPG (GURPS, D&D, genérico...).
- Entrar na mesa = entra no estado realtime (LiveKit room + Django Channels group).

### 3.2 Tela única de jogo (P0)
Layout dockável/redimensionável. Painel mestre contém:
- Strip de **câmeras** (jogadores + GM) com indicador de quem está falando.
- **Chat** com rolagem registrada, mensagens whisper, comandos `/r`, `/skill`, `/rule`.
- **Ficha ativa** (do personagem do jogador, ou da que o GM está controlando).
- **Mapa/VTT** dockável central.
- **Journal** acessível via aba.
- **Radio** (Watch Together) recolhível.

Nada disso causa navegação.

### 3.3 Chat + sistema de dados (P0)
- Rolagem por sintaxe textual: `/r 3d6`, `/r 4d6kh3+2`, `/r 1d20+str`, `/r skill spada`.
- Rolagens disparadas por **clique em campo da ficha** (atributo, skill, dano, etc.).
- Resultado mostrado pra todos (ou apenas pro GM, se `--private`).
- **Multi-sistema desde o início**: motor de dice agnóstico; cada sistema define seus modificadores e fórmulas via descritor JSON.
- Whisper, mensagens IC/OOC, comandos especiais.

### 3.4 Áudio e vídeo (P0)
- **LiveKit self-hosted** como SFU. Roda no WSL2 ao lado do Django.
- Múltiplas **tracks de áudio por usuário** (voz, board sounds, música).
- GM tem **mixer**: pode mutar canais específicos, ajustar volume por canal, dispar board sounds para todos.
- Push-to-talk com atalho global (Tauri).
- Indicador visual de quem está falando.
- Configuração de dispositivo (mic/cam/speaker) com preview.

### 3.5 Watch Together (Radio) (P1)
- Modo A: **YouTube IFrame API** com sync de play/pause/seek via Channels. Rápido, leve.
- Modo B: **Screen-share via LiveKit** (fallback quando YouTube bloqueia embed). GM compartilha tela/aba.
- GM alterna entre modos. Toggle por "cena".

### 3.6 VTT (Virtual Tabletop) avançado (P1)
- Camadas: background, terrain, tokens, GM-only, drawing.
- Grid configurável: quadrado, hexagonal (flat/pointy), gridless.
- Tokens arrastáveis com snap ao grid. Status effects (ícones), HP/FP bar opcional, visão por token.
- **Fog of war** revelável pelo GM com "brush".
- **Dynamic lighting** baseada em paredes/obstáculos definidos pelo GM. Visão computada por token.
- Ferramentas de desenho (linha, retângulo, texto, freehand) com cores e camadas.
- Régua de medição em unidades do sistema (squares/hexes/metros).
- Upload de imagem como background; assets em MinIO.
- Importação de **mapas mundi** com escala configurável.

### 3.7 Fichas dinâmicas (P0)
- Schema **multi-sistema**: ficha = template (definido pelo sistema RPG) + valores (instance).
- Template define campos, fórmulas, rolagens disparáveis, layouts.
- Players editam só a própria ficha (com aprovação do GM em campos críticos, opcional).
- **HP/FP atualizam em tempo real** pra todos na mesa.
- Clíque em "Atributo X" -> rola já com os modificadores do template.
- Suporte a vantagens/desvantagens com efeitos mecânicos (V2: efeitos são decorativos; aplicação automática em V3+).

### 3.8 Journal compartilhado (P1)
- Estrutura tipo wiki: páginas, sub-páginas, tags.
- Suporta texto (markdown), imagens, links cruzados para fichas/mapas/mensagens do chat.
- Permissões: público da mesa, gm-only, jogador-X-only (notas privadas).
- Búsca full-text + semântica via RAG (reaproveita o motor descrito em `CHATBOT_BLUEPRINT.md`).

### 3.9 Gravação e resumo de sessão (P1)
- **LiveKit Egress** grava o composite (ou tracks individuais) em arquivo na MinIO.
- Whisper.cpp transcreve localmente.
- Ollama (modelo local) gera **resumo estruturado**: timeline de eventos, decisões, NPCs encontrados, loot, ganchos abertos.
- Opt-in por sessão (controle do GM).

### 3.10 Chatbot RAG (P1)
- Já implementado no app `rag/`. Integrar como comando `/rule` no chat e como painel lateral.
- A V2 expande pra cobrir não só regras (PDFs), mas estado vivo da mesa (V-2 do app rag).

### 3.11 Distribuição como app (P0)
- **Tauri desde o início**. Build gera `.exe` (Windows), `.dmg` (Mac), `.AppImage` (Linux).
- App aponta para a URL Cloudflare Tunnel do servidor (configurável; o GM passa pros amigos).
- Atalhos globais: push-to-talk (F-key), mostrar/esconder ficha, foco no chat.
- Notificação do SO: "sua vez", "mensagem privada do GM", "alguem entrou na mesa".
- Auto-update via Tauri updater (JSON hosteado no Cloudflare/MinIO).

### 3.12 Acesso remoto (P0)
- **Cloudflare Tunnel** saindo da máquina do owner. URL estável tipo `mesa.roll3d6.com`.
- Sem mexer no roteador residencial.
- HTTPS automático via Cloudflare.

---

## 4. Restrições invioláveis

1. **Site em produção não pode quebrar.** Migrações aditivas/transformadoras, nunca destrutivas. Deploys em sequência controlada.
2. **Nada de API paga recorrente.** OpenAI, Anthropic, Daily.co, LiveKit Cloud estão **fora** até o owner pedir explicitamente.
3. **Preservar dados existentes** (users, fichas, campanhas, mensagens, saves). ETL completo.
4. **Idioma de comunicação e UI: pt-BR.**
5. **Performance e custo de banda importam.** Cloudflare Tunnel é free até limites generosos; LiveKit consome banda do owner — dimensionar com isso em mente.
6. **Trabalho por fases.** Cada V valida antes de avançar.
7. **Documentação atualizada.** Quando uma decisão muda, atualiza o `.md` correspondente — não cria novo.
8. **Compatibilidade com WSL2 + Windows host** do owner (especificações em `memory/user_dev_env.md`).
9. **Single-page experience.** Nada de páginas que recarregam durante a sessão ativa.
10. **Paridade dev/prod completa.** Postgres 16 + pgvector + Redis + MinIO + LiveKit + Ollama rodam **tanto em DEV (WSL2 local) quanto em PROD (GCP VM)**. Proibido SQLite, in-memory channel layer, filesystem-only storage ou qualquer atalho que crie divergência. Toda feature que funciona em dev tem que funcionar em prod sem surpresa de driver, transação, índice ou tipo de coluna (`JSONField`, `VectorField`, etc.). Migrations rodadas em dev = mesmas que vão pra prod.

---

## 5. Decisões fechadas (com motivo)

| # | Decisão | Por quê |
|---|---|---|
| D1 | **Evolução incremental** do site Django, não reescrita do backend | Site em prod há anos, models estáveis, allauth funcionando. Risco/recompensa ruim de trocar Django. |
| D2 | **Frontend SPA em React + Vite + TypeScript** | Ecossistema enorme para realtime, canvas (VTT), WebRTC, drag-and-drop. Única escolha séria pro escopo. |
| D3 | **Backend continua Django 5.x + Channels** sobre Redis. ASGI via daphne | Já é o stack. Channels resolve realtime sem novo serviço. |
| D4 | **LiveKit self-hosted** como SFU de áudio/vídeo | Free, controle total de tracks/canais, escala até dezenas de usuários numa room. Roda no WSL2 do owner. |
| D5 | **YouTube IFrame API + screen-share** (toggle) pro Watch Together | Cobre os dois casos: video aberto e vídeo restrito. Sync via Channels. |
| D6 | **VTT avançado** com lighting, hex, fog — PixiJS como engine de canvas | Pixi tem performance para milhares de sprites/lights. React reaproveita via `@pixi/react`. |
| D7 | **Multi-sistema desde o início** | Owner quer suportar além de GURPS. Schema genérico template+instance evita refazer ficha depois. |
| D8 | **MinIO self-hosted** como object storage | API S3 padrão, free, migra pra cloud real sem mudar código. Centraliza assets pesados. |
| D9 | **Tauri desde o início** para distribuição desktop | Atalhos globais, notificações, icóne nativo. Binário leve. Reaproveita 100% do código React. |
| D10 | **Cloudflare Tunnel** para acesso remoto | Free, sem mexer no roteador, HTTPS grátis, URL estável. |
| D11 | **Gravação LiveKit + Whisper local + Ollama** | Zero custo recorrente. GPU local acelera Whisper e Ollama. |
| D12 | **RAG já implementado** (`rag/` app) integra como `/rule` no chat + painel | Reaproveitamento direto; não duplicar trabalho. |
| D13 | **Desktop-first responsive**; mobile só visual | VTT/multi-cam exige tela grande. Mobile PWA cobre chat/ficha. |
| D14 | **Backend permanece monolito Django**; não quebrar em microserviços | 1 dev, complexidade extra não paga. Serviços externos são LiveKit, Redis, Postgres, MinIO, Ollama — todos via Docker Compose. |
| D15 | **Postgres + pgvector em DEV e PROD** (paridade total). Sem SQLite em dev | TI agora autoriza Postgres local. Evita classe inteira de bugs "funciona em dev / quebra em prod" (JSON, transações, índices, pgvector). Realtime/Channels precisa Redis em ambos os ambientes pelo mesmo motivo. |
| D16 | **Django REST Framework (DRF)** como API framework | Padrão de mercado, ecossistema maduro, integração natural com allauth e permissões. Verbosidade compensa em projetos longevos. |
| D17 | **Auth por sessão cookie do allauth** (não JWT) | Reaproveita login existente sem reinventar. Tauri usa webview → cookie funciona. Cloudflare Tunnel preserva cookie. CSRF via header `X-CSRFToken`. |
| D18 | **Monorepo único** com `frontend/` dentro do repo Django atual | 1 dev, PRs cobrem stack inteira, evita sync entre repos. `src-tauri/` mora dentro de `frontend/`. Backend Python continua na raiz. |

Decisões ainda **abertas** estão na seção 12.

---

## 6. Stack alvo

### Frontend (cliente)
- **React 18+** com Vite, TypeScript estrito.
- **TailwindCSS** + Radix UI (ou shadcn/ui) para componentes acessíveis.
- **TanStack Query** para data fetching.
- **Zustand** ou **Jotai** para estado local; **Yjs** ou **Liveblocks-style** para colaboração realtime (decisão aberta — seção 12).
- **react-rnd** ou **dockview** para janelas dockáveis.
- **PixiJS** via `@pixi/react` para o VTT.
- **LiveKit client SDK** (`livekit-client` + `@livekit/components-react`).
- **YouTube IFrame API** wrapper.
- **Tauri** v2 para empacotamento desktop.

### Backend
- **Django 5.x** + **Channels 4** + **daphne** (ASGI).
- **Postgres 16** + **pgvector** (RAG).
- **Redis 7** (Channels layer + cache + sessões LiveKit auth).
- **MinIO** (object storage S3-compat).
- **LiveKit Server** (SFU). 
- **Ollama** (LLM local).
- **Whisper.cpp** (transcrição).
- API REST com DRF (ou Django Ninja) + WebSocket via Channels.

### DevOps / distribuição
- **Docker Compose** pra subir o servidor inteiro localmente.
- **Cloudflared** (Tunnel daemon) rodando junto.
- **Tauri build** gera binários pros três SOs.
- Atualizações de binário servidas via MinIO público + JSON updater.

---

## 7. Topologia de deployment

```
┌────────────────────────────────┐
│  Jogador remoto                      │
│  Tauri app  ────HTTPS/WSS──────┐  │
└──────────────────────────────│──┘
                                  ▼
                       ┌──────────────────────┐
                       │ Cloudflare Edge        │
                       │ (Tunnel termination)   │
                       └─────────┬────────────┘
                                 │ tunnel
                                 ▼
┌────────────────────────────────────────┐
│  Máquina do owner (Windows + WSL2)              │
│                                                 │
│  ┌─ Windows host ──────────────────┐   │
│  │ cloudflared (tunnel)                  │   │
│  │ Ollama (GPU)                          │   │
│  └────────────────────────────────────┘   │
│  ┌─ WSL2 Ubuntu ───────────────────┐   │
│  │ docker compose:                       │   │
│  │   - daphne (Django+Channels) :8000   │   │
│  │   - postgres+pgvector         :5432  │   │
│  │   - redis                     :6379  │   │
│  │   - minio (S3)                :9000  │   │
│  │   - livekit                   :7880  │   │
│  │   - whisper-worker (Python)          │   │
│  └────────────────────────────────────┘   │
└────────────────────────────────────────┘
```

- **Cloudflare Tunnel** termina HTTPS na borda e entrega no daphne via túnel.
- LiveKit usa WebRTC sobre TURN (Cloudflare Tunnel não suporta UDP nativamente; precisa TURN over TCP/443). Detalhar na V-1.
- Postgres em produção (GCP VM) continua intocado durante a transição.

---

## 8. Plano de fases (V-0 → V-7)

### V-0 — Fundação (semana 1-2)
- Repo: criar diretório `frontend/` para a SPA React + Vite + TS.
- `docker-compose.yml` na raiz com Postgres, Redis, MinIO, LiveKit (modo dev).
- Endpoint Django `/api/` consolidado (DRF ou Django Ninja).
- Auth JWT (ou sessão cookie compartilhada com allauth).
- CORS configurado.
- Smoke test: SPA loga, faz `GET /api/me/`, recebe perfil.

### V-1 — Lobby + ficha básica (semana 3-4)
- Tela de listagem de campanhas (read-only).
- Abrir campanha = entra na "tela única" placeholder.
- Ficha do personagem (read-only) renderizada via template descritor.
- ETL inicial: confirmar que dados existentes do site antigo aparecem.

### V-2 — Chat + dice engine (semana 5-6)
- WebSocket via Channels.
- Engine de dados agnóstica: sintaxe `XdY`, modificadores, target-number, success/failure.
- Mensagens persistidas; rolagens têm DTO especial (com breakdown).
- Comandos `/r`, `/whisper`, `/rule` (esse último chama o RAG existente).

### V-3 — Ficha editavel + click-to-roll (semana 7-8)
- Players editam própria ficha.
- Clicar em atributo dispara rolagem.
- HP/FP atualizam em tempo real (broadcast via Channels).

### V-4 — LiveKit áudio/vídeo (semana 9-11)
- Servidor LiveKit no docker-compose.
- Token de room emitido pelo Django (assinado).
- Strip de câmeras na tela.
- Mixer básico (mute/volume por usuário).
- Push-to-talk no browser.
- TURN sobre TCP/443 para passar Cloudflare Tunnel.

### V-5 — VTT básico (semana 12-14)
- PixiJS canvas dockável.
- Upload de imagem como background.
- Grid configurável.
- Tokens com drag-and-drop. Sync via Channels.
- Régua de medição.

### V-6 — Watch Together (semana 15)
- YouTube IFrame API + sync de play/pause/seek.
- Screen-share via LiveKit como alternativa.

### V-7 — Journal + tauri (semana 16-18)
- Journal wiki-like com markdown + imagens em MinIO.
- Empacotamento Tauri: binários pros 3 SOs.
- Atalhos globais básicos.
- Auto-update setup.

### V-8+ — Avanços do VTT (mês 5+)
- Fog of war.
- Dynamic lighting.
- Grid hex.
- Visão por token.
- Camadas GM-only.

### V-9+ — Gravação e resumo (mês 6+)
- LiveKit Egress.
- Whisper worker.
- Ollama summarization.

### V-10+ — Polimento e mobile responsive
- Layout responsive para chat/ficha em telas pequenas.
- Tema visual definitivo.
- Notificações Tauri.

---

## 9. Modelo de dados (esboço)

Reusa o que existe e adiciona:

```
RPGSystem (GURPS, D&D 5e, Generic...)
  - id, name, slug, description

CharacterSheetTemplate (definido por sistema)
  - rpg_system FK
  - schema (JSON: campos, fórmulas, layout, rolagens disparáveis)
  - version

CharacterSheet (instance)
  - template FK
  - owner FK (User)
  - campanha FK
  - values (JSON)
  - hp_current, hp_max, fp_current, fp_max  -- denormalizados pra realtime

Campanha (existente; adicionar)
  - rpg_system FK
  - active_scene FK (Scene)

Scene
  - campanha FK
  - name
  - vtt_config (JSON: grid, dimensões, layers)
  - background_asset FK

Token (no VTT)
  - scene FK
  - character_sheet FK (opcional)
  - x, y, layer
  - status_effects (JSON)
  - vision_config (JSON)

VTTAsset
  - campanha FK
  - kind (background, token, drawing)
  - storage_path (MinIO)

JournalPage
  - campanha FK
  - parent FK self
  - title, body_md
  - visibility (public, gm_only, user_only)

Message (chat) (existente; adicionar)
  - kind (text, roll, system, whisper)
  - payload (JSON com breakdown de rolagem)

DiceRoll (denormalizado pra histórico)
  - message FK
  - formula, result, breakdown, target_number, outcome

SessionRecording
  - campanha FK
  - started_at, ended_at
  - composite_path (MinIO)
  - transcript_path (MinIO)
  - summary_md
```

Detalhes finos ficam para a fase de implementação de cada V.

---

## 10. Migração de dados

Estratégia: **espelhamento + cut-over**.

1. Schema novo coexiste com o antigo (apps separadas se necessário).
2. Comando `manage.py migrate_legacy` faz ETL:
   - Users do `auth_user` migram intactos (já são do mesmo schema).
   - `CharacterSheet` antigo -> novo (mapeamento template GURPS).
   - `Campanha`, `Message`, `SaveState` migram preservando timestamps.
3. Site antigo continua no ar até V2 estar estável.
4. Cut-over: rota `app.roll3d6.com` aponta pro novo; antigo vira `legacy.roll3d6.com` read-only por 60 dias.

---

## 11. Gotchas conhecidos e mitigações

- **Cloudflare Tunnel não passa UDP** -> LiveKit precisa fallback TURN/TCP-443. Configurar `livekit-server` com `rtc.use_external_ip` e `turn.tcp_port: 443`.
- **WSL2 IP muda no reboot** -> portproxy + tarefa agendada Windows (já documentada em `SESSION_STATE.md`).
- **Tauri Windows sem code-sign** -> SmartScreen alerta na primeira vez. Documentar fluxo "Mais informações → Executar". Orçar code-sign futuro.
- **Banda residencial limitada** -> SFU é eficiìnte mas 8 webcams 720p = ~4 Mbps up. Conservador.
- **WebRTC + Cloudflare Tunnel + LiveKit** é frontier; precisa de smoke test cedo (V-4).
- **Realtime state divergence** entre clientes do VTT -> CRDT (Yjs) ou autoridade do servidor (decisão pendente).
- **Multi-sistema vs UI polida**: schema genérico tende a UI genérica. Mitigar com renderers por sistema (GURPS tem seu render-set, D&D tem outro).

---

## 12. Questões ainda abertas (perguntar ao owner antes de codar V-2+)

1. **Estado realtime do VTT**: Yjs (CRDT, robusto a desconexões) ou autoridade Django (mais simples, requer reconciliation)?
2. **Sintaxe de dados**: adotar dicedef padrão de Roll20/Foundry (`/r 2d6+1d4`) ou criar DSL própria?
3. **Auth no Tauri**: usar `localhost` callback OAuth ou device-code flow?
4. **DRF vs Django Ninja**: preferência? Django Ninja tem melhor DX, DRF tem mais legado.
5. **Estado do Tauri quando servidor offline**: app fecha, fica em loop de retry, ou tem modo offline read-only para fichas?
6. **Layout dockável**: `dockview` (mais pro), `react-mosaic` (mais simples)?
7. **Theming**: tema visual definitivo (cores, tipografia, vibe — épico/dark/medieval/sci-fi)?
8. **Voice activity**: VAD client-side (rapido, varia por device) ou server-side (mais preciso, mais carga)?
9. **GM vs Player vs Spectator**: spectator (só vê/ouve) entra no escopo? Convidados sem conta?
10. **Backup**: snapshot diário do Postgres + MinIO pra onde? B2/Wasabi (free tier) ou disco USB físico?

---

## 13. Como o owner trabalha (perfil)

- **Único desenvolvedor**, perfil de arquiteto/dev sêlnior.
- Máquina: Dell Precision 3591, Windows 10 corp + WSL2 com root, RTX 1000 Ada (4GB VRAM).
- Idioma: pt-BR.
- Não quer custos recorrentes em APIs.
- Evita autoindent em editores (problemas históricos colando código).
- Prefere trabalho por fases com smoke test ao final de cada uma.
- Não quer recomeçar do zero; quer evoluir o existente.
- Mais detalhes em `memory/user_dev_env.md` e `memory/project_current_goal.md` no sistema de memória do agente.

---

## 14. Documentos relacionados (no repo)

- `CLAUDE.md` — índice primário.
- `docs/SESSION_STATE.md` — onde o trabalho atual parou (dev local + RAG).
- `docs/AGENT_PROMPT.md` — prompt do agente para o projeto atual (V1).
- `docs/RAG_ARCHITECTURE.md` — arquitetura do chatbot RAG (reutilizado na V2).
- `docs/CHATBOT_BLUEPRINT.md` — blueprint portável do RAG.
- `docs/GURPS_KNOWLEDGE.md` — base de conhecimento GURPS.
- **Este documento** — prompt do arquiteto da V2.

---

## 15. Como o agente deve começar

Ao receber este prompt, na próxima sessão:

1. Confirmar que leu este documento integralmente.
2. Verificar o estado atual do repo (`git status`, leitura de `SESSION_STATE.md`).
3. **Fazer todas as perguntas da seção 12** que ainda fizerem sentido.
4. Listar **adaptações ou riscos não cobertos aqui** que você identificar.
5. Só depois disso, propor um plano de execução da V-0 com checklist concreto.
6. Implementar V-0 e validar com smoke test reproduzível antes de seguir.

Nunca pular pra V-1 sem V-0 verde. Nunca implementar V-5 (VTT) antes de V-4 (LiveKit) validado.
