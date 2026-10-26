# Blueprint — Chatbot RAG local (reutilizável em outros projetos)

> **Como usar este documento**
>
> Abra-o noutro projeto/sessão de Claude Code e diga:
> *"Leia `CHATBOT_BLUEPRINT.md` e implemente esse mesmo sistema neste projeto, adaptando ao stack daqui. Antes de codar, confirme as adaptações comigo."*
>
> Este blueprint descreve a arquitetura, as decisões já tomadas (com motivos) e a sequência de implementação que funcionou no projeto roll3d6 RPG (Django + Postgres + pgvector + Ollama). Os princípios e o pipeline são portáveis pra qualquer stack web.

---

## 0. Briefing pro agente

Você é o engenheiro de software encarregado de implementar um **chatbot RAG local** dentro de uma aplicação web já existente. O sistema responde perguntas em linguagem natural sobre:

1. **Conteúdo estático** (PDFs, manuais, base de conhecimento) — fonte autoritativa.
2. **Estado vivo da aplicação** (entidades do banco) — opcional na V-1; necessário a partir da V-2.

Princípios invioláveis:

1. **Tudo local, zero custo recorrente.** Embedder e LLM rodam na máquina do usuário. Nada de OpenAI/Anthropic API a menos que o usuário levante o tema explicitamente.
2. **Nunca remover campos/dados de models existentes.** Migrations são aditivas ou transformadoras, nunca destrutivas. Aplicação está em produção.
3. **Não recomeçar do zero.** Evolua o que já existe. Identifique convenções, leia config, reaproveite.
4. **Mudanças estruturais (nova app, novo serviço, troca de banco) exigem confirmação do usuário antes de codar.**
5. **Trabalho por etapas (V-0 → V-5).** Conclua e valide uma antes de avançar.
6. **Idioma: pt-BR.** Responda e documente em português.
7. **Performance importa.** Tráfego/CPU custam. Top-K pequeno, contexto pequeno, modelo pequeno por padrão.
8. **Avoid premature abstractions.** Três linhas similares > abstração precoce. Sem feature flags hipotéticos.

---

## 1. O que é o sistema

Pipeline RAG (Retrieval-Augmented Generation):

```
pergunta NL  →  embedding  →  busca top-K em pgvector
                                      │
                                      ▼
                              chunks relevantes (com refs)
                                      │
                                      ▼
                              prompt estruturado  →  LLM local (Ollama)  →  resposta + refs
```

**O que entrega:**
- Endpoint HTTP que recebe `{question, ...filtros}` e devolve resposta sintetizada + fontes.
- UI mínima (uma página HTML) pra testar/usar.
- CLI de management pra ingestão e debug.

**O que NÃO entrega na primeira versão:**
- Auth/CSRF reforçados (V-5).
- Re-embedding em tempo real do banco (V-2).
- Métricas/observabilidade (backlog).

---

## 2. Arquitetura alvo (dev local)

```
┌────────────────────────────────┐        ┌────────────────────────────────┐
│ Windows host                   │        │ WSL2 Ubuntu  (ou Linux nativo) │
│ ─────────────────────────────  │        │ ─────────────────────────────  │
│ Ollama nativo (CUDA)           │ ←HTTP→ │ App web + ASGI server          │
│   - qwen2.5:3b-instruct        │ :11434 │ Postgres 16 + pgvector         │
│   - usa GPU (4GB+ VRAM ok)     │        │ Python 3.13 venv               │
│                                │        │ sentence-transformers (CPU)    │
└────────────────────────────────┘        │ pymupdf (extração PDF)         │
                                          └────────────────────────────────┘
```

Pra **servir na LAN** (outros PCs):
- Windows: `netsh interface portproxy` redireciona `0.0.0.0:8000` → `WSL2:8000`.
- Firewall: regra inbound TCP 8000.
- Tarefa agendada re-aplica o portproxy no boot (IP do WSL muda).

Detalhes operacionais completos em `docs/SESSION_STATE.md` deste repo.

---

## 3. Decisões fechadas (com motivos)

| # | Decisão | Por quê |
|---|---|---|
| D1 | **pgvector** dentro do Postgres existente | Zero serviço novo. Joins com tabelas do app. Backup unificado. |
| D2 | Embedder único: **`paraphrase-multilingual-mpnet-base-v2`** (768 dims) | Multilingual decente em pt-BR. Roda em CPU em <100ms/chunk. ~500MB RAM. |
| D3 | LLM de síntese: **Ollama + `qwen2.5:3b-instruct`** | 3b cabe em GPU 4GB. Qualidade boa em pt-BR. Streaming nativo. Free. |
| D4 | **Sem API paga** (OpenAI, Anthropic) por padrão | Custo recorrente é o que o usuário evitou explicitamente. Quality gap ~10-15% é aceitável. |
| D5 | Chunking **paragraph-aware** ~300 tokens (min 50, max 500) | Quebrar em parágrafo preserva semântica. 300 tokens ≈ 1 idéia compacta. |
| D6 | **Top-K = 3** default; `num_ctx = 2048`; `num_predict = 400` | Prompt grande mata CPU. Em GPU dá pra subir, mas 3 chunks resolve a maior parte. |
| D7 | **Streaming NDJSON** no endpoint | Usuário vê progresso. Timeout de 600s no client tolera CPU lento. |
| D8 | Embedding de entidades do banco fica para **V-2** (Django signals) | V-1 já entrega valor: regras estáticas. DB embeddings são incremento. |
| D9 | **Permissão obrigatória** no retrieval de entidades (V-2) | Manager customizado filtra `campanha_id` + `scope`. Nenhuma view pode pular. |
| D10 | Hash de chunk pra **idempotência de ingestão** | Re-rodar `ingest_books` não duplica. Só insere o que mudou. |

---

## 4. Stack mínimo

- **Backend:** Python 3.13, framework web do projeto (Django 5.x no caso roll3d6; adapte).
- **DB:** Postgres 16 + extensão `vector` (pgvector ≥ 0.8).
- **Embedder:** `sentence-transformers` (carregado como singleton no startup).
- **Extração PDF:** `pymupdf` (alias `fitz`). Evite `pdftotext`/poppler — quebra em distros antigas.
- **LLM:** Ollama nativo no host com GPU. Comunica via HTTP `/api/generate` com `stream=true`.
- **Frontend:** vanilla JS + `fetch` com `ReadableStream` pra ler NDJSON. Sem framework pesado na V-1.

Deps Python extras:
```
psycopg[binary]>=3.2
pgvector
sentence-transformers
pymupdf
```

---

## 5. Modelos de dados

App isolada: `rag/` (separada do app principal — é infraestrutura).

```python
# rag/models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from pgvector.django import VectorField, HnswIndex

EMBED_DIM = 768  # casa com paraphrase-multilingual-mpnet-base-v2

class RuleChunk(models.Model):
    book          = models.CharField(max_length=200)
    chapter       = models.CharField(max_length=200, null=True, blank=True)
    section       = models.CharField(max_length=200, null=True, blank=True)
    page_start    = models.PositiveIntegerField()
    page_end      = models.PositiveIntegerField()
    text          = models.TextField()
    text_hash     = models.CharField(max_length=64, db_index=True)
    tokens        = models.PositiveIntegerField()
    embedding     = VectorField(dimensions=EMBED_DIM)
    embedding_model = models.CharField(max_length=100,
                                       default="paraphrase-multilingual-mpnet-base-v2")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("book", "text_hash")]
        indexes = [
            HnswIndex(name="rulechunk_emb_hnsw",
                      fields=["embedding"],
                      m=16, ef_construction=64,
                      opclasses=["vector_cosine_ops"]),
        ]

class EntityEmbedding(models.Model):
    SCOPE_CHOICES = [("public", "public"), ("campanha", "campanha"), ("gm_only", "gm_only")]

    content_type   = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id      = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # ADAPTE: troque "gurps.Campanha" pelo agrupador-de-permissão do seu projeto
    campanha       = models.ForeignKey("gurps.Campanha", null=True, blank=True,
                                       on_delete=models.CASCADE)
    scope          = models.CharField(max_length=20, choices=SCOPE_CHOICES, default="public")
    text           = models.TextField()
    source_hash    = models.CharField(max_length=64, db_index=True)
    embedding      = VectorField(dimensions=EMBED_DIM)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("content_type", "object_id")]
        indexes = [
            HnswIndex(name="entityemb_hnsw",
                      fields=["embedding"],
                      m=16, ef_construction=64,
                      opclasses=["vector_cosine_ops"]),
        ]
```

---

## 6. Pipeline de ingestão de PDFs

Comando de management `ingest_books`:

1. Varre `books/*.pdf` (path configurável via `--books-dir`).
2. Para cada PDF, abre com `fitz.open(path)`.
3. Para cada página, extrai texto (`page.get_text("text")`).
4. **Chunk paragraph-aware**:
   - Split em parágrafos (`\n\n`).
   - Acumula até `target_tokens` (~300). Se ultrapassar `max_tokens` (500), corta.
   - Descarta chunks com menos de `min_tokens` (50).
   - Tokenização rápida: `len(text.split())` é suficiente; o embedder tem seu próprio tokenizer.
5. Computa `text_hash = sha256(chunk_text)`. Se `(book, text_hash)` já existe, skip.
6. Embed em batch (32-64 chunks por vez): `model.encode(texts, normalize_embeddings=True)`.
7. Bulk insert.

Flags úteis: `--reset` (apaga RuleChunk antes), `--book "Nome"` (só um livro), `--books-dir`.

```python
# rag/embeddings.py — singleton
from functools import lru_cache
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(MODEL_NAME)

def embed_texts(texts: list[str]) -> list[list[float]]:
    vecs = get_model().encode(texts, normalize_embeddings=True,
                              batch_size=32, show_progress_bar=False)
    return vecs.tolist()
```

---

## 7. Retrieval

```python
# rag/query.py
from pgvector.django import CosineDistance
from .models import RuleChunk
from .embeddings import embed_texts

DEFAULT_TOP_K = 3

def search_rules(question: str, top_k: int = DEFAULT_TOP_K, book: str | None = None):
    qvec = embed_texts([question])[0]
    qs = RuleChunk.objects.all()
    if book:
        qs = qs.filter(book=book)
    return list(
        qs.annotate(distance=CosineDistance("embedding", qvec))
          .order_by("distance")[:top_k]
    )
```

Para `EntityEmbedding`, **sempre** aplique filtro de permissão antes da busca vetorial. Implemente em um `Manager` customizado que recebe `user` e/ou `campanha_id` e nunca permita query crua.

---

## 8. Síntese (Ollama)

```python
# rag/synthesis.py
import json
import requests
from django.conf import settings

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:3b-instruct"

PROMPT_TEMPLATE = """Você é um assistente que responde dúvidas sobre {dominio}.
Responda APENAS com base nos trechos abaixo. Se a resposta não estiver neles,
diga que não encontrou. Cite a referência (livro, página) ao final.

TRECHOS:
{trechos}

PERGUNTA: {pergunta}

RESPOSTA (em pt-BR, objetiva):"""

def build_prompt(question, chunks, dominio="as regras do sistema"):
    trechos = "\n\n".join(
        f"[{c.book} p.{c.page_start}] {c.text}" for c in chunks
    )
    return PROMPT_TEMPLATE.format(dominio=dominio, trechos=trechos, pergunta=question)

def synthesize_stream(question, chunks, model=DEFAULT_MODEL, ollama_url=None):
    url = ollama_url or getattr(settings, "OLLAMA_URL", DEFAULT_OLLAMA_URL)
    payload = {
        "model": model,
        "prompt": build_prompt(question, chunks),
        "stream": True,
        "options": {
            "num_ctx": 2048,
            "num_predict": 400,
            "temperature": 0.2,
        },
    }
    with requests.post(url, json=payload, stream=True, timeout=600) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if data.get("response"):
                yield data["response"]
            if data.get("done"):
                break
```

> **Importante:** sempre leia `OLLAMA_URL` de `settings`, nunca hardcode `localhost`. No WSL2 a URL precisa apontar pro IP do Windows host (detectar em runtime via `ip route | awk '/^default/ {print $3}'`).

---

## 9. Endpoint + UI

**View streaming (Django ASGI):**

```python
# rag/views.py
import json
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .query import search_rules
from .synthesis import synthesize_stream

@csrf_exempt
@require_POST
def query_api(request):
    body = json.loads(request.body)
    question = body["question"]
    top_k = int(body.get("top_k", 3))
    model = body.get("model", "qwen2.5:3b-instruct")

    chunks = search_rules(question, top_k=top_k)

    def gen():
        yield json.dumps({"type": "refs", "refs": [
            {"book": c.book, "page": c.page_start, "distance": float(c.distance)}
            for c in chunks
        ]}) + "\n"
        for token in synthesize_stream(question, chunks, model=model):
            yield json.dumps({"type": "token", "text": token}) + "\n"
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingHttpResponse(gen(), content_type="application/x-ndjson")
```

**UI mínima (HTML + vanilla JS):** input pra pergunta + select de model + select de top_k + área de resposta + lista de refs. JS lê `response.body.getReader()` e parseia NDJSON linha a linha. Mostra refs em cima e tokens streaming em baixo.

---

## 10. Plano de etapas

| Etapa | Entrega | Critério de aceitação |
|---|---|---|
| **V-0** | App `rag` criada, models + migration aplicada, deps instaladas, pgvector habilitado | `python manage.py migrate` passa, `\dx` mostra `vector` no Postgres |
| **V-1** | `ingest_books` funcionando; PDFs vivem em `RuleChunk` | Contagem de chunks > 1000; busca por título de capítulo retorna o chunk certo |
| **V-1.1** | (opcional) OCR pra PDFs imagem-only via tesseract | GM Screen ou equivalente vira chunks |
| **V-2** | `EntityEmbedding` populado via signals `post_save`/`post_delete`. Manager com filtro de permissão | Editar uma entidade re-embed em <2s; teste verifica que user A não enxerga entidade de user B |
| **V-3** | `search_rules` + CLI `query_rules` + endpoint `/rag/api/query` streaming | `time python manage.py query_rules "..."` < 8s em GPU |
| **V-3.1** | UI HTML mínima em `/rag/` | Funciona em browser, mostra refs + tokens streaming |
| **V-3.2** | Tuning: top_k, num_ctx, modelos opcionais (1.5b/3b/7b) | Latência aceitável (<10s) e respostas coerentes |
| **V-4** | (backlog) Síntese via Claude API com prompt caching | Só se usuário aprovar custo |
| **V-5** | Auth + CSRF + rate limit no endpoint | Login obrigatório; rate por usuário |

---

## 11. Restrições e gotchas (lições aprendidas)

- **Ubuntu EOL** (focal etc.) tem repos PGDG quebrados — baixe `.deb` de `jammy` à mão se necessário.
- **WSL2 não tem systemd por padrão** — use `sudo service postgresql start`. Pra `systemd`, habilite em `/etc/wsl.conf`.
- **IP do WSL2 muda a cada reboot do Windows** — pra port forwarding LAN, agende script PowerShell que re-aplica `netsh portproxy` no boot.
- **Ollama no Windows escuta só em localhost por padrão** — setar variável de **sistema** `OLLAMA_HOST=0.0.0.0:11434` e reiniciar o serviço.
- **`nano` com autoindent corrompe Python colado** — use `nano -I` sempre, ou edite via IDE/Claude.
- **Multi-line heredoc colado no terminal Windows quebra** — prefira `git pull` ou `printf ... | tee` em vez de `cat <<EOF`.
- **Primeiro embedding load é lento** (~30s baixando + carregando modelo). Subsequentes <100ms.
- **CPU-only LLM na nuvem (4 vCPUs) → 1-3 min por query.** Inviável interativo. Por isso GPU local.
- **Top-K alto + num_ctx alto explodem o prompt em CPU.** Mantenha conservador.
- **Embedding hash precisa versionar com `embedding_model`** — se trocar modelo, re-ingerir tudo.
- **Encoding UTF-16 BOM** em `requirements.txt` (gerado por PowerShell `>`) quebra `pip` no Linux. Converta com `iconv -f UTF-16 -t UTF-8`.

---

## 12. Checklist de bring-up (resumo)

> Versão completa com comandos exatos para o projeto roll3d6 está em `docs/SESSION_STATE.md`. Use como referência.

1. Postgres + pgvector + Redis (se houver Channels) instalados e rodando.
2. Banco criado, extensão `vector` habilitada, usuário com perms.
3. `venv` + `pip install -r requirements.txt` + deps RAG (psycopg, pgvector, sentence-transformers, pymupdf).
4. App `rag` criada, models, migration aplicada.
5. Ollama instalado no host com GPU; `ollama pull qwen2.5:3b-instruct`; `OLLAMA_HOST=0.0.0.0:11434`.
6. `local_settings.py` com `OLLAMA_URL` apontando pro host correto.
7. PDFs disponíveis; rodar `ingest_books`.
8. `query_rules "pergunta de teste"` retorna em <8s.
9. Daphne/Uvicorn em `0.0.0.0:8000`; `/rag/` abre no browser.
10. (Pra LAN) firewall + portproxy + ALLOWED_HOSTS configurados.

---

## 13. Trocas de stack — adaptações comuns

Se o outro projeto **não é Django**, mantenha a arquitetura e troque:

- **FastAPI / Flask:** modelos viram SQLAlchemy + `pgvector.sqlalchemy.Vector`. Endpoint vira `StreamingResponse` (FastAPI) ou `Response(stream_with_context(...))` (Flask).
- **Node.js / Next.js:** use `pg` + extensão `pgvector`. Embedder via `@xenova/transformers` (roda em Node) ou microserviço Python isolado. Streaming via `ReadableStream`.
- **Sem Postgres:** alternativas — Qdrant, Weaviate, Chroma. Perde-se o join com dados do app; ganha-se filtros vetoriais mais ricos. Só vale a pena se já houver outro DB principal.
- **Sem GPU local:** baixe pra modelo menor (`qwen2.5:1.5b-instruct` ou `phi3:mini`) e aceite respostas mais curtas/menos precisas, ou use API paga (com aprovação do usuário).

A ordem das etapas e os princípios não mudam. Só a sintaxe.

---

## 14. O que pedir ao agente em cada turno

- **Turno 1:** "Leia `CHATBOT_BLUEPRINT.md`. Antes de codar, liste as adaptações necessárias pra este projeto (stack, paths, modelo de permissão) e pergunte o que não estiver claro."
- **Turno 2:** "Implemente V-0 (app + models + migration + deps). Pare antes de V-1 pra eu validar."
- **Turno 3:** "V-1 — `ingest_books`. Teste com 1 PDF pequeno antes de processar tudo."
- **Turno 4:** "V-3 — retrieval + endpoint streaming + UI mínima. Sem auth ainda."
- **Turno 5+:** V-2 (entidades), V-5 (auth), tuning.

Sempre encerre cada etapa com smoke test reproduzível antes de avançar.
