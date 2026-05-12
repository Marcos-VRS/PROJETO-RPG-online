# Estado da Execução V2 — onde paramos

> **Atualizar a cada bloco de trabalho concluído.** Este documento é a fonte da verdade do "onde estamos agora".
>
> **Última atualização:** 2026-05-12.

---

## Fase atual: **F-1 — Reorganização do repo + Docker Compose** (em andamento)

### Contexto da execução
- Owner está no **PC empresa** (sem WSL2 com admin local, sem Docker rodando).
- Estratégia: **adiantar tudo que é arquivo/código** (F-1 estrutural + F-2 estrutural). Commitar e pushar.
- Em casa, no Dell Precision com WSL2 e admin: rodar **F-0** (instalações) e validar com `docker compose up`.

### Domínio confirmado
- `roll3d6rpg.com` na Cloudflare.

---

## Progresso F-1 (estrutural, sem execução de stack)

Legenda: ✅ feito · 🔄 em andamento · ⏳ pendente · ⛔ bloqueado

| # | Subtarefa | Status |
|---|---|---|
| 1 | Branch `feat/v2-foundation` criada | ✅ |
| 2 | DRF + pgvector + psycopg no `requirements.txt`; criado `requirements-ml.txt` | ✅ |
| 3 | `settings.py` env-driven (Postgres+Redis+DRF+CORS+CSRF dev/prod) | ✅ |
| 4 | App `api/` com `MeView`, `CsrfView`, `HealthView` | ✅ |
| 5 | `api/urls.py` ligado em `project/urls.py` | ✅ |
| 6 | `docker-compose.yml` na raiz (postgres+redis+minio+livekit+web, healthchecks) | ✅ |
| 7 | `Dockerfile` + `.dockerignore` | ✅ |
| 8 | `.env.example` documentado | ✅ |
| 9 | `.gitignore` atualizado (frontend, Tauri, volumes) | ✅ |
| 10 | Scaffold `frontend/` (package.json, tsconfig, vite, tailwind, src/, README) | ✅ |
| 11 | Este doc criado | ✅ |
| 12 | `CLAUDE.md` atualizado com novos docs V2 | ✅ |
| 13 | Commit + push da branch (`5c00c3e`) | ✅ |

---

## O que **NÃO** está feito ainda (proposital)

Estas etapas dependem da máquina pessoal com admin/WSL2 e ficam pra próxima sessão (em casa):

- **F-0 inteira**: instalação de Postgres+pgvector+Redis no WSL2, Docker no WSL2, Node 20, Rust, cloudflared no Windows, túnel `roll3d6-dev`.
- **F-1 execução**: `docker compose up`, primeiro `migrate`, smoke test de admin via localhost:8000.
- **F-2 instalação**: `pnpm install` no `frontend/`, `pnpm dev`, login allauth ponta-a-ponta.

---

## Próximo passo concreto após o `git pull` em casa

```bash
# dentro do WSL2 do Dell Precision
cd ~/roll3d6rpgdev          # ou clonar se ainda não tem
git pull
git checkout feat/v2-foundation

# (executar F-0 antes — ver docs/PLATFORM_V2_EXECUTION_PLAN.md)
# depois:
cp .env.example .env
# editar .env com senhas reais
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

# em outro terminal
cd frontend
pnpm install
pnpm dev
```

Critério de aceitação da F-1 (em casa):
- `docker compose ps` mostra postgres, redis, minio, livekit, web saudáveis
- `curl http://localhost:8000/admin/` retorna 302
- `http://localhost:9001` abre console MinIO
- SPA em `http://localhost:5173` mostra "Não autenticado" e link de login

---

## Decisões e mudanças desde o último update

- **Requirements separado em dois arquivos:** `requirements.txt` (base + Django + DRF + psycopg + pgvector) e `requirements-ml.txt` (sentence-transformers, pymupdf). Permite imagens mais leves em prod no futuro se quiser separar serviço RAG.
- **Postgres é default no `settings.py`** (não mais SQLite). Falha rápida se senha não estiver configurada. `local_settings.py` continua disponível pra override.
- **`api/HealthView` (`/api/health/`) sem auth** — útil pro healthcheck do Compose e pro Cloudflare Tunnel.
- **`extra_hosts: host.docker.internal:host-gateway`** no compose pra Linux/WSL2 conseguirem chamar Ollama no host.
- **Endpoints na ordem em `urls.py`**: `admin/` > `api/` > `rag/` > `accounts/` > `""` (gurps legado por último). Site antigo (htmx) continua funcionando em paralelo durante a transição.

---

## Pontos de atenção que viraram TODO durante a execução

- [ ] **Validar `requirements.txt`** após primeiro `pip install` em casa — versões de `pgvector`, `psycopg[binary]` e `sentence-transformers` foram fixadas com base em estabilidade, podem precisar ajuste.
- [ ] **Confirmar que `gurps/` continua funcionando** com Postgres em vez de SQLite (V1 estava em SQLite localmente; agora paridade exige Postgres). Pode precisar de algum ajuste em queries específicas se houver alguma incompatibilidade.
- [ ] **`gurps/consumers.py`** e routing de Channels não tocados — validar na F-5 quando entrarmos no chat WS.
- [ ] **LiveKit em `--dev` mode** funciona pra F-0..F-6 local. Antes da F-7 produção, gerar chaves reais e config TURN/TCP-443 pra Cloudflare Tunnel.
- [ ] **Tauri toolchain** não testado ainda — F-3 vai exigir Rust + libs nativas instaladas.
