# Session State — onde parei e como continuar

> **Última sessão:** 2026-04-21 (noite).
> **Próxima sessão:** migração completa do dev pra WSL2 local.
>
> Quando voltar, leia este documento primeiro.

---

## Decisão ativa: pivô pra dev local (WSL2 + Ollama no Windows host)

Decidido em 2026-04-21 ao final do dia. O dev estava na VM do GCP (4 vCPUs, sem GPU), mas a inferência LLM do RAG ficava em 1-3 min por query — inutilizável interativamente. A TI da empresa bloqueia instalações na conta Windows "normal" do usuário, mas **ele tem WSL2 instalado com acesso root**. Todo o dev migra pra lá.

**Produção (GCP VM, IP 35.239.231.110) continua intocada.** O site segue no ar normalmente.

---

## Status das etapas V-0 até V-4

| Etapa | Descrição | Status |
|---|---|---|
| V-0.0 | Postgres em dev | ✅ no GCP VM (dev `roll3d6_dev`) / ⏳ refazer no WSL2 |
| V-0 | App Django `rag` + models + pgvector | ✅ commit `d48500e` (scaffold) + `a4b3ea3` (migration) |
| V-1 | Ingestão PDFs → `RuleChunk` | ✅ 3 livros, 3124 chunks, 768 dims (local embedder) |
| V-2 | Embeddings de entidades do banco | ⏳ não começado |
| V-3 | Retrieval semântico (`search_rules`) + CLI `query_rules` | ✅ commit `6f0ea25` |
| V-3.1 | Síntese via Ollama (streaming) | ✅ commits `909d34e` / `1f6f8b2` |
| V-3.2 | Endpoint HTTP + página HTML `/rag/` | ✅ commit `670c365` |
| V-3.3 | Perf tuning (top_k=3, num_ctx=2048, 1.5b/3b/7b opcionais) | ✅ commit `aceec0d` |
| V-4 | Síntese via Claude API | 📌 backlog (custo) |

Hashes estão na history do repo. Commit mais recente relevante: `aceec0d`.

---

## O que está no repo hoje

- `rag/` — app completa: models, chunking, embeddings locais, síntese via Ollama, retrieval, CLI commands, view HTTP, template HTML.
- `rag/management/commands/` — `ingest_books`, `query_rules`, `bench_ollama`.
- `gurps/` — app principal do site (inalterada exceto pelo ccccc.py scratch que NÃO deve ser commitado).
- `project/settings.py` — `"rag"` em `INSTALLED_APPS`.
- `project/urls.py` — `rag.urls` montado em `/rag/`.
- `docs/` — AGENT_PROMPT, RAG_ARCHITECTURE, GURPS_KNOWLEDGE, este SESSION_STATE, e subpastas por tema (atributos GURPS em `docs/gurps/attributes.md`).
- `gurps/data/` — catálogo estruturado GURPS (`attributes.json`, `advantages.json` parcial).
- `books/` — gitignored; PDFs ficam só no ambiente local.
- `CLAUDE.md` — índice principal.

---

## Arquitetura local alvo (WSL2 + Windows host)

```
┌────────────────────────────────┐        ┌────────────────────────────────┐
│ Windows host                   │        │ WSL2 Ubuntu                    │
│ ─────────────────────────────  │        │ ─────────────────────────────  │
│ Ollama nativo (CUDA)           │ ←HTTP→ │ Django + daphne                │
│   - qwen2.5:3b-instruct        │ :11434 │ Postgres 16 + pgvector         │
│   - usa GPU RTX 1000 Ada (4GB) │        │ Python 3.13 venv               │
│                                │        │ sentence-transformers (CPU)    │
└────────────────────────────────┘        │ pymupdf, openai (não usa),     │
                                          │ anthropic (não usa), pgvector  │
                                          └────────────────────────────────┘
```

- **Django/Postgres/embeddings ficam no WSL2.** A GPU não é necessária pra embedder (CPU já é rápido pra 300 chunks).
- **Ollama fica no Windows host.** Só ele precisa da GPU, e o driver NVIDIA está no Windows.
- **Django chama Ollama via HTTP** através do gateway entre WSL2 e host.

---

## Plano pra primeira sessão no WSL2

### 1. Preparar o WSL2 (Ubuntu)

```bash
# dentro do WSL2
sudo apt update
sudo apt install -y postgresql postgresql-contrib postgresql-16-pgvector python3.13 python3.13-venv python3.13-dev git build-essential
```

(Se `postgresql-16` não estiver disponível na distro, aceitar 14 ou 15 — pgvector funciona em todas.)

### 2. Criar o banco dev

```bash
sudo -u postgres psql -c "CREATE USER roll3d6_dev WITH PASSWORD 'ESCOLHA_UMA_SENHA';"
sudo -u postgres psql -c "CREATE DATABASE roll3d6_dev OWNER roll3d6_dev ENCODING 'UTF8' TEMPLATE template0;"
sudo -u postgres psql -d roll3d6_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d roll3d6_dev -c "GRANT ALL ON SCHEMA public TO roll3d6_dev;"
```

### 3. Clonar repo e criar venv

```bash
cd ~
git clone git@github.com:Marcos-VRS/PROJETO-RPG-online.git roll3d6rpgdev
cd roll3d6rpgdev
python3.13 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install 'psycopg[binary]>=3.2' pgvector sentence-transformers pymupdf
```

> Se a chave SSH do WSL2 não estiver cadastrada no GitHub, use HTTPS ou gere uma nova chave (ed25519) e cadastre antes.

### 4. Configurar segredos

```bash
cat > ~/.roll3d6_secrets <<'EOF'
export ROLL3D6_DEV_DB_PASSWORD='<senha do banco dev>'
EOF
chmod 600 ~/.roll3d6_secrets
echo '[ -f "$HOME/.roll3d6_secrets" ] && source "$HOME/.roll3d6_secrets"' >> ~/.bashrc
source ~/.bashrc
```

### 5. `project/local_settings.py`

Conteúdo (não commitar — já está no `.gitignore`):

```python
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "roll3d6_dev",
        "USER": "roll3d6_dev",
        "PASSWORD": os.environ.get("ROLL3D6_DEV_DB_PASSWORD", ""),
        "HOST": "localhost",
        "PORT": "5432",
    }
}

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

# Windows host Ollama — IP ou hostname visto de dentro do WSL2.
# Descobrir com:  ip route | awk '/^default/ {print $3}'
# Exemplo: 172.29.224.1
OLLAMA_URL = "http://<WINDOWS_HOST_IP>:11434/api/generate"
```

**Necessário**: atualizar `rag/synthesis.py` pra respeitar essa variável `settings.OLLAMA_URL` em vez de usar `localhost:11434` hardcoded. Ajuste de 3 linhas; fazer na próxima sessão.

### 6. Instalar Ollama no Windows

Baixar instalador nativo em https://ollama.com/download/windows e rodar.

Ollama no Windows escuta só em `localhost` por padrão. Pra aceitar conexões do WSL2, setar a variável de ambiente `OLLAMA_HOST=0.0.0.0:11434` no Windows (Painel de Controle → Sistema → Variáveis de Ambiente) e reiniciar o serviço.

Depois:

```powershell
ollama pull qwen2.5:3b-instruct
```

### 7. Copiar os livros pra estrutura acessível

Opção A: deixar em `C:\Users\...\PROJETO-RPG-online\books` e apontar via `--books-dir /mnt/c/Users/.../PROJETO-RPG-online/books`.
Opção B: copiar pra dentro do WSL2 `~/roll3d6rpgdev/books/` (mais rápido, duplica).

### 8. Migrations + ingestão

```bash
cd ~/roll3d6rpgdev
source .venv/bin/activate
python manage.py migrate
python manage.py ingest_books  # ou --books-dir /mnt/c/...
```

### 9. Testar

```bash
time python manage.py query_rules "qual o custo da Visao Aguçada?"
```

Expectativa (GPU via Ollama Windows): **2-8 segundos** por query.

```bash
python manage.py runserver 0.0.0.0:8000
```

Abrir no navegador Windows: http://localhost:8000/rag/

---

## Próximas coisas depois que o ambiente local estiver funcional

Em ordem sugerida:

1. **V-2 — Embeddings de entidades do banco.** Signals `post_save`/`post_delete` em CharacterSheet, Campanha, Message etc. Re-embed em tempo real via `rag.embeddings`. Model `EntityEmbedding` já existe; falta só popular + criar `search_entities` + integrar no endpoint.
2. **Migrar embedder pra `BAAI/bge-m3`** (se qualidade de retrieval continuar marginal). Modelo maior, melhor em PT-BR, 1024 dims. Requer migration + re-ingestão dos 3 livros.
3. **Catalogar mais GURPS.** Etapa 2 (Vantagens) ficou em 30 entradas A-C. Faltam D-Z + desvantagens + skills + modificadores + combate. Ver [`docs/GURPS_KNOWLEDGE.md`](GURPS_KNOWLEDGE.md).
4. **OCR do GM Screen.** É só imagem; precisa tesseract. Pode ser V-1.1.
5. **Auth + CSRF** no endpoint `/rag/api/query` (atualmente `@csrf_exempt`, sem login).

---

## Detalhes operacionais guardados

- **Chave OpenAI**: o usuário tem uma (sem crédito no momento). Está no `~/.roll3d6_secrets` da VM GCP. **Não é usada** desde o pivô pra embeddings locais, mas fica guardada.
- **Chave SSH GCP VM**: `~/.ssh/id_ed25519` no WSL2 precisa ser gerada e cadastrada se quiser acessar a VM da máquina nova. A chave antiga que está no Windows host não é vista de dentro do WSL2 (embora o `~/.ssh/` seja montado de `/mnt/c/Users/<user>/.ssh/` em alguns setups).
- **Banco de produção no GCP** (`roll3d6_data_base`): NÃO copiado pra dev. Se quiser dados realistas pra testar, fazer `pg_dump` do prod e `pg_restore` no dev.
