# Plano de Execução — Roll3d6 V2

> **Companion document de `PLATFORM_V2_PROMPT.md`.** O prompt descreve o **quê** e o **porquê**; este documento descreve o **como** e o **quando**.
>
> **Última atualização:** 2026-05-12.
> **Regra:** nunca pular uma fase sem o checklist de aceitação verde.

---

## Visão geral das fases

| Fase | Nome | Entrega-fim | Estimativa | Bloqueia |
|---|---|---|---|---|
| **F-0** | Pré-flight (TI + WSL2 + Postgres + Docker + Cloudflare) | Ambiente DEV completo, paridade com PROD | 1 dia | Tudo |
| **F-1** | Reorganização do repo + Docker Compose | `docker compose up` sobe stack inteira em dev | 2-3 dias | F-2+ |
| **F-2** | API DRF + bootstrap React/Vite/TS | SPA "Hello, {user}" autenticado via allauth | 3-4 dias | F-3+ |
| **F-3** | Tauri wrapper | `.exe` instalável que abre a SPA | 2 dias | F-7 |
| **F-4** | Lobby + ficha read-only via API | Listar campanhas/fichas no SPA | 1 semana | F-5+ |
| **F-5** | Chat WS + dice engine | `/r 3d6`, mensagens persistidas, broadcast | 1 semana | F-6+ |
| **F-6** | Ficha editável + click-to-roll + HP/FP realtime | Editar ficha pela SPA, rolar do clique | 2 semanas | F-7+ |
| **F-7** | LiveKit áudio/vídeo + Cloudflare Tunnel | Strip de câmeras + mixer básico, acessível remotamente | 2-3 semanas | F-8+ |
| **F-8** | VTT básico (PixiJS) | Imagem + grid + tokens drag-and-drop | 2-3 semanas | F-9 |
| **F-9** | Watch Together | YouTube sync + screen-share fallback | 1 semana | F-10 |
| **F-10** | Journal | Wiki pages com markdown + imagens MinIO | 1-2 semanas | F-11+ |
| **F-11** | Migração de dados | ETL completo prod→nova schema | 1 semana | Go-live V2 |
| **F-12+** | VTT avançado, gravação, mobile responsive, polimento | A planejar | meses | — |

Estimativas são pessimistas-realistas para 1 dev part-time. Acelera quando virar foco principal.

---

## F-0 — Pré-flight (Ambiente DEV)

### Objetivo
Sair de "máquina nova, TI presente" para "WSL2 com Postgres+Redis+Docker funcionando, comunicação com Ollama no Windows host, espelhando exatamente o que vai rodar em PROD".

### Pré-requisitos
- [ ] TI fisicamente presente.
- [ ] Owner com `sudo` no WSL2.
- [ ] Conexão de internet.

### Checklist (segue o passo-a-passo de `SESSION_STATE.md` + extras pra Docker)

1. **`[WIN-ADMIN]` Ollama** — etapa 1 do bring-up de chatbot.
2. **`[WIN-ADMIN]` Firewall** — etapa 2 (porta 8000).
3. **`[WSL]` Sistema base** — etapa 3 (build-essential, python3.13, git).
4. **`[WSL]` Postgres + pgvector + Redis** — etapa 4.
5. **`[WSL]` Docker Engine no WSL2:**
   ```bash
   sudo apt install -y ca-certificates curl gnupg
   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   sudo chmod a+r /etc/apt/keyrings/docker.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
     | sudo tee /etc/apt/sources.list.d/docker.list
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker $USER
   newgrp docker
   docker run hello-world
   ```
6. **`[WSL]` Node.js 20 (LTS)** + pnpm — pro frontend:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt install -y nodejs
   sudo npm i -g pnpm
   node -v && pnpm -v
   ```
7. **`[WSL]` Rust toolchain** — pro Tauri:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
   source "$HOME/.cargo/env"
   sudo apt install -y libwebkit2gtk-4.1-dev build-essential libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
   ```
8. **`[WSL]` Clonar repo + venv** — etapa 5.
9. **`[WSL]` Secrets + `local_settings.py`** — etapa 6.
10. **`[WSL]` Copiar livros** — etapa 7.
11. **`[WSL]` Patch `rag/synthesis.py`** — etapa 8.
12. **`[WSL]` Migrations + ingestão RAG** — etapa 9. **Não é necessário pro F-1, mas valida que o ambiente está completo.**
13. **`[WIN-ADMIN]` cloudflared no Windows host:**
    ```powershell
    winget install --id Cloudflare.cloudflared
    cloudflared tunnel login
    cloudflared tunnel create roll3d6-dev
    # Anotar o UUID do tunnel
    ```
    Criar `C:\Users\marcos.vinicius\.cloudflared\config.yml`:
    ```yaml
    tunnel: <UUID>
    credentials-file: C:\Users\marcos.vinicius\.cloudflared\<UUID>.json
    ingress:
      - hostname: dev.roll3d6.SEU_DOMINIO.com
        service: http://localhost:8000
      - service: http_status:404
    ```
    Apontar DNS no Cloudflare:
    ```powershell
    cloudflared tunnel route dns roll3d6-dev dev.roll3d6.SEU_DOMINIO.com
    ```
    Rodar:
    ```powershell
    cloudflared tunnel run roll3d6-dev
    ```

### Critério de aceitação
- [ ] `docker run hello-world` funciona no WSL2 sem `sudo`.
- [ ] `node -v` ≥ 20, `pnpm -v` ≥ 9.
- [ ] `cargo --version` funciona.
- [ ] `psql -U roll3d6_dev -d roll3d6_dev -c "SELECT 1;"` retorna `1`.
- [ ] `redis-cli ping` retorna `PONG`.
- [ ] `curl http://$(ip route | awk '/^default/ {print $3}'):11434/api/tags` retorna lista de modelos Ollama (do WSL2 chamando Windows host).
- [ ] `cloudflared tunnel info roll3d6-dev` lista o túnel rodando.
- [ ] (Opcional, valida a pilha RAG) `python manage.py query_rules "teste"` retorna resposta < 8s.

### Riscos / mitigações
- **WSL2 sem systemd** → instalar `systemd` via `/etc/wsl.conf` ou usar `service`.
- **Docker dentro do WSL2 sem Docker Desktop** → setup acima usa Docker Engine direto, não depende do Docker Desktop. Funciona.
- **Cloudflare exige domínio próprio** → owner precisa ter um domínio gerenciado pela Cloudflare. Custo: ~R$50/ano em registrar. **Alternativa free**: `cloudflared tunnel --url http://localhost:8000` gera URL `https://xyz.trycloudflare.com` (efêmera, não estável). Bom pra dev, ruim pra prod.

---

## F-1 — Reorganização do repo + Docker Compose

### Objetivo
Trazer a stack inteira pra Docker Compose, criar diretório `frontend/` vazio, e validar que Django legado continua subindo.

### Passos

1. **Branch nova:** `git checkout -b feat/v2-foundation`

2. **Criar `docker-compose.yml` na raiz:**
   ```yaml
   services:
     postgres:
       image: pgvector/pgvector:pg16
       environment:
         POSTGRES_DB: roll3d6_dev
         POSTGRES_USER: roll3d6_dev
         POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"

     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data

     minio:
       image: minio/minio:latest
       command: server /data --console-address ":9001"
       environment:
         MINIO_ROOT_USER: ${MINIO_ROOT_USER}
         MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
       ports:
         - "9000:9000"
         - "9001:9001"
       volumes:
         - minio_data:/data

     livekit:
       image: livekit/livekit-server:latest
       command: --dev --bind 0.0.0.0
       ports:
         - "7880:7880"
         - "7881:7881"
         - "7882:7882/udp"

   volumes:
     postgres_data:
     redis_data:
     minio_data:
   ```

3. **Criar `.env.example`** na raiz (commitado):
   ```
   POSTGRES_PASSWORD=mudar
   MINIO_ROOT_USER=admin
   MINIO_ROOT_PASSWORD=mudar123
   DJANGO_SECRET_KEY=mudar
   OLLAMA_URL=http://172.29.224.1:11434/api/generate
   ```
   E `.env` (gitignored) com valores reais.

4. **Migrar Postgres local pra o do compose:**
   - Parar `service postgresql stop`. (Vamos usar só o do Docker daqui em diante.)
   - Atualizar `local_settings.py` pra apontar pro `localhost:5432` (que agora é o container).
   - `docker compose up -d postgres`
   - `psql -h localhost -U roll3d6_dev -d roll3d6_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"`

5. **Atualizar `settings.py` pra ler do environment** (`os.environ`):
   ```python
   import os
   from pathlib import Path
   # ...
   SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure")
   DATABASES = {
       "default": {
           "ENGINE": "django.db.backends.postgresql",
           "NAME": os.environ.get("POSTGRES_DB", "roll3d6_dev"),
           "USER": os.environ.get("POSTGRES_USER", "roll3d6_dev"),
           "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
           "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
           "PORT": "5432",
       }
   }
   ```
   (Mantém `local_settings.py` pra override em dev, mas o default já vai pelo env.)

6. **Criar `Dockerfile` pra Django:**
   ```dockerfile
   FROM python:3.13-slim
   WORKDIR /app
   RUN apt-get update && apt-get install -y --no-install-recommends \
       build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   RUN pip install --no-cache-dir 'psycopg[binary]>=3.2' pgvector sentence-transformers pymupdf
   COPY . .
   CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "project.asgi:application"]
   ```

7. **Adicionar serviço `web` ao compose:**
   ```yaml
   web:
     build: .
     env_file: .env
     environment:
       POSTGRES_HOST: postgres
       REDIS_HOST: redis
     depends_on:
       - postgres
       - redis
     ports:
       - "8000:8000"
     volumes:
       - .:/app
       - books:/app/books
   ```

8. **Criar `frontend/`** vazio + `.gitkeep`. Adicionar `frontend/node_modules/`, `frontend/dist/`, `frontend/src-tauri/target/` no `.gitignore`.

9. **Adicionar `CHANGELOG.md`** na raiz, registrar V-2 start.

10. **Smoke test:**
    ```bash
    docker compose up -d
    docker compose exec web python manage.py migrate
    docker compose exec web python manage.py createsuperuser
    curl http://localhost:8000/admin/   # 302 → login
    ```

### Critério de aceitação
- [ ] `docker compose up -d` sobe Postgres, Redis, MinIO, LiveKit e web sem erro.
- [ ] `python manage.py migrate` aplica todas as 54 migrações existentes.
- [ ] Login admin funciona em http://localhost:8000/admin/.
- [ ] MinIO console acessível em http://localhost:9001/.
- [ ] Branch `feat/v2-foundation` pusheada.

### Riscos
- **Volume `.:/app` em WSL2 é lento por causa de filesystem cross-mount.** Mitigação: clonar repo em `~/` (caminho Linux nativo), não em `/mnt/c/`. Já é a recomendação.
- **`requirements.txt` UTF-16 BOM** quebra `pip` no Dockerfile. Converter antes do primeiro build (já documentado em `SESSION_STATE.md`).

---

## F-2 — API DRF + bootstrap React/Vite/TS

### Objetivo
SPA mínima rodando em `http://localhost:5173`, conectando à API Django em `http://localhost:8000/api/`, fazendo login (allauth) e mostrando `"Hello, {username}"`.

### Passos

1. **Backend — instalar DRF:**
   ```bash
   docker compose exec web pip install djangorestframework django-cors-headers
   echo "djangorestframework==3.15.2" >> requirements.txt
   echo "django-cors-headers==4.7.0" >> requirements.txt
   ```

2. **Configurar `settings.py`:**
   ```python
   INSTALLED_APPS += ["rest_framework", "corsheaders"]
   MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", *MIDDLEWARE]

   REST_FRAMEWORK = {
       "DEFAULT_AUTHENTICATION_CLASSES": [
           "rest_framework.authentication.SessionAuthentication",
       ],
       "DEFAULT_PERMISSION_CLASSES": [
           "rest_framework.permissions.IsAuthenticated",
       ],
   }

   CORS_ALLOWED_ORIGINS = [
       "http://localhost:5173",
       "http://localhost:1420",  # Tauri dev
   ]
   CORS_ALLOW_CREDENTIALS = True
   CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://localhost:1420"]
   ```

3. **Criar app `api/`:**
   ```bash
   docker compose exec web python manage.py startapp api
   ```
   Em `api/views.py`:
   ```python
   from rest_framework.views import APIView
   from rest_framework.response import Response
   from rest_framework.permissions import AllowAny, IsAuthenticated

   class MeView(APIView):
       permission_classes = [IsAuthenticated]
       def get(self, request):
           u = request.user
           return Response({"id": u.id, "username": u.username, "email": u.email})

   class CsrfView(APIView):
       permission_classes = [AllowAny]
       def get(self, request):
           from django.middleware.csrf import get_token
           return Response({"csrfToken": get_token(request)})
   ```
   Em `api/urls.py`:
   ```python
   from django.urls import path
   from .views import MeView, CsrfView
   urlpatterns = [
       path("me/", MeView.as_view()),
       path("csrf/", CsrfView.as_view()),
   ]
   ```
   Incluir em `project/urls.py`: `path("api/", include("api.urls"))`.

4. **Frontend — bootstrap:**
   ```bash
   cd frontend
   pnpm create vite . --template react-ts
   pnpm install
   pnpm add @tanstack/react-query axios zustand react-router-dom
   pnpm add -D tailwindcss@latest postcss autoprefixer
   pnpm add -D @types/node
   pnpm dlx tailwindcss init -p
   ```

5. **Configurar Tailwind** em `tailwind.config.js`:
   ```js
   export default {
     content: ["./index.html", "./src/**/*.{ts,tsx}"],
     theme: { extend: {} },
     plugins: [],
   };
   ```
   `src/index.css`:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

6. **Cliente API** em `frontend/src/lib/api.ts`:
   ```ts
   import axios from "axios";

   export const api = axios.create({
     baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
     withCredentials: true,
     xsrfCookieName: "csrftoken",
     xsrfHeaderName: "X-CSRFToken",
   });

   export async function ensureCsrf() {
     await api.get("/csrf/");
   }
   ```

7. **App** em `frontend/src/App.tsx`:
   ```tsx
   import { useQuery } from "@tanstack/react-query";
   import { api, ensureCsrf } from "./lib/api";
   import { useEffect } from "react";

   export default function App() {
     useEffect(() => { ensureCsrf(); }, []);
     const { data, isLoading, error } = useQuery({
       queryKey: ["me"],
       queryFn: async () => (await api.get("/me/")).data,
       retry: false,
     });
     if (isLoading) return <div className="p-8">Carregando...</div>;
     if (error) return (
       <div className="p-8">
         <p>Não autenticado.</p>
         <a className="text-blue-600 underline" href="http://localhost:8000/login/?next=/admin/">
           Fazer login
         </a>
       </div>
     );
     return <div className="p-8 text-2xl">Olá, {data.username}!</div>;
   }
   ```
   E `main.tsx` envelopando com `QueryClientProvider`.

8. **`.env` do frontend** em `frontend/.env.local`:
   ```
   VITE_API_URL=http://localhost:8000/api
   ```

9. **Smoke test:**
   ```bash
   # terminal 1 (raiz)
   docker compose up
   # terminal 2 (frontend)
   cd frontend && pnpm dev
   ```
   Abrir `http://localhost:5173`. Deve cair em "Não autenticado". Clicar no link, logar via allauth no Django, voltar para o `:5173` → "Olá, X!".

### Critério de aceitação
- [ ] `/api/me/` retorna 403 sem sessão, 200 com.
- [ ] CSRF token vem via cookie + header funciona.
- [ ] CORS habilitado pra `:5173`.
- [ ] SPA mostra usuário logado depois do allauth login.
- [ ] Build do frontend (`pnpm build`) gera `dist/` sem erro.

### Riscos
- **CSRF + CORS + credentials é a parte mais chata.** Errar `withCredentials` ou `CSRF_TRUSTED_ORIGINS` faz pedido falhar silenciosamente.
- **Sessão entre :8000 e :5173 funciona em dev por estar no mesmo `localhost`.** Em prod (atrás de Cloudflare) tudo está no mesmo domínio.

---

## F-3 — Tauri wrapper

### Objetivo
Gerar um `.exe` (e `.AppImage` se possível no WSL) que abre uma janela contendo a SPA.

### Passos

1. **`cd frontend && pnpm dlx @tauri-apps/cli@latest init`**
   - App name: `Roll3d6`
   - Window title: `Roll3d6`
   - Web assets relative to project: `..` (caminho do `dist/`)
   - Dev server URL: `http://localhost:5173`
   - Frontend dev command: `pnpm dev`
   - Frontend build command: `pnpm build`

2. **Configurar `frontend/src-tauri/tauri.conf.json`:**
   - `productName`: "Roll3d6"
   - `identifier`: "com.roll3d6.app"
   - `build.devUrl`: `http://localhost:5173`
   - `app.windows`: tamanho mínimo 1280x720, título "Roll3d6"
   - `app.security.csp`: definir CSP permissiva pra dev, restritiva pra build

3. **Hardcode da URL do backend em prod** (apontará pra Cloudflare Tunnel):
   - Variável `VITE_API_URL` no `.env.production` aponta pra `https://dev.roll3d6.SEU_DOMINIO.com/api`.
   - O Tauri build usa essa variável quando empacota.

4. **Build e teste:**
   ```bash
   cd frontend
   pnpm tauri dev      # abre janela com hot reload
   pnpm tauri build    # gera .exe em src-tauri/target/release/bundle/
   ```

### Critério de aceitação
- [ ] `pnpm tauri dev` abre janela mostrando a SPA com hot reload.
- [ ] `pnpm tauri build` gera `.exe` (Windows) sem erro.
- [ ] `.exe` executado abre janela e renderiza a SPA contra `http://localhost:8000` (em dev).

### Riscos
- **Tauri build no WSL2 não gera `.exe`** (precisa Windows). Solução: rodar `pnpm tauri build` numa shell PowerShell, com Node e Rust instalados no Windows também. **Alternativa**: GitHub Actions com matrix de OSes (V2.1).
- **Code-sign** ausente → SmartScreen alerta. Documentar fluxo "Mais informações → Executar mesmo assim" para amigos. Orçar code-sign pago futuramente.

---

## F-4 → F-11 (sumário)

Cada uma terá seu próprio mini-plano quando chegarmos lá. Esboço:

### F-4: Lobby + ficha read-only
- Serializers DRF pra `Campanha`, `CharacterSheet`.
- Endpoint `GET /api/campanhas/` (lista pra user logado).
- `GET /api/campanhas/{id}/`, `GET /api/character-sheets/{id}/`.
- React: rotas `/lobby`, `/campanha/:id`, componente `<CharacterSheet readonly />`.

### F-5: Chat WS + dice engine
- Consumer WebSocket via Channels (já tem `gurps/consumers.py`).
- Model `Message` ganha `kind`, `payload (JSON)`.
- `rag/dice/` novo módulo: parser de fórmula, executor, JSON breakdown.
- Comando `/r XdY`, `/rule <pergunta>` (chama RAG).
- React: componente `<Chat />` com input + lista + scroll.

### F-6: Ficha editável + click-to-roll + HP/FP realtime
- Endpoints PATCH na ficha.
- Click em atributo dispara `POST /api/dice/roll/` com contexto da ficha.
- Broadcast via Channels: `hp_changed`, `fp_changed` → react-query invalida.

### F-7: LiveKit + Cloudflare Tunnel
- Endpoint `POST /api/livekit/token/` emite token assinado.
- LiveKit server config: TURN/TCP/443 pra passar Cloudflare.
- `@livekit/components-react` na SPA.
- Mixer básico: mute/volume por usuário.
- Push-to-talk com `keydown` global (V3 vira atalho do SO via Tauri).

### F-8: VTT básico (PixiJS)
- Modelos `Scene`, `Token`, `VTTAsset`.
- Endpoint para upload de asset → MinIO presigned URL.
- React: componente `<VTT />` com `@pixi/react`.
- Sync de tokens via Channels (debounce de 100ms na movimentação).

### F-9: Watch Together
- Modelo `ScenePlayback` (kind: youtube|screen, current_time, paused, source).
- Channels event `playback_changed`.
- React: `<RadioYouTube>` com YouTube IFrame API + `<RadioScreenShare>` via LiveKit track de tela.

### F-10: Journal
- Modelos `JournalPage`, `JournalAttachment`.
- DRF endpoints.
- React: editor markdown (`@uiw/react-md-editor`) + upload MinIO.

### F-11: Migração de dados
- Comando `manage.py migrate_legacy`.
- Mapeia user, ficha, campanha, mensagens, savestate.
- Hard cut em prod: rota nova → `app.roll3d6.com`; antiga → `legacy.roll3d6.com` read-only.

---

## Cronograma sugerido (calendário)

Assumindo dedicação part-time (~10-15h/semana):

```
Semana 1:   F-0 (1 dia intensivo com TI) + começa F-1
Semana 2:   F-1 (Docker Compose) + start F-2
Semana 3-4: F-2 (API + SPA)
Semana 5:   F-3 (Tauri)
Semana 6-7: F-4 (Lobby + ficha read-only)
Semana 8-9: F-5 (Chat + dice)
Semana 10-12: F-6 (Ficha editável + realtime)
Semana 13-15: F-7 (LiveKit + Tunnel)
Semana 16-18: F-8 (VTT básico)
Semana 19:  F-9 (Watch Together)
Semana 20-21: F-10 (Journal)
Semana 22:  F-11 (Migração)
Semana 23:  Cut-over PROD V2
Semanas 24+: VTT avançado, gravação, polimento (F-12+)
```

Total: **~6 meses pra V2 com features P0+P1 entregues**. Aceitável pra escopo descrito.

---

## Regras de execução

1. **Cada F termina com checklist verde.** Não passa pra próxima sem aceitação.
2. **Branch por F:** `feat/v2-fX-nome-curto`. Merge em `main` após smoke test.
3. **Commit por subtarefa.** Mensagens descritivas em pt-BR.
4. **CHANGELOG atualizado** ao fim de cada F.
5. **Site antigo intocado** até F-11. Em paralelo, prod no GCP segue rodando.
6. **Cada F que toca infra exige documentação** atualizada no `.md` correspondente.
7. **Confirmar com owner antes de:**
   - Adicionar dependência pesada não listada aqui.
   - Refatorar parte de código fora do escopo da F atual.
   - Mudar schema de model existente de forma destrutiva.

---

## Próximas decisões a tomar antes de cada F

| F | Decisão pendente |
|---|---|
| F-0 | Domínio Cloudflare confirmado? Ou usar `trycloudflare.com` efêmero pra dev? |
| F-2 | Tema visual da SPA (cores, tipografia, vibe)? |
| F-5 | Sintaxe de dice: copiar Roll20 ou DSL própria? |
| F-7 | TURN externo (Coturn) ou usar o embutido do LiveKit? |
| F-8 | Estado realtime do VTT: Yjs (CRDT) ou autoridade servidor? |
| F-11 | Janela de manutenção pro cut-over: dia/horário? |

Cada decisão fica aberta até a F correspondente.

---

## Como começar agora

Se você (owner) topa o plano:

1. **Marcar dia com TI** (F-0 precisa dele presente — Ollama install + firewall + portproxy).
2. **Comprar/confirmar domínio Cloudflare** (pode ficar pra depois se aceitar URL `trycloudflare.com` no dev).
3. **Próxima conversa comigo:** "vamos pra F-1" → eu começo a criar `docker-compose.yml`, `Dockerfile` e a reorganização do repo.

Antes disso, três coisas que eu **preciso confirmar**:

