# Arquitetura RAG — busca semântica sobre regras e estado do jogo

> Documento vivo. Atualizar conforme a implementação evoluir. Decisões foram tomadas em **2026-04-21**.

---

## Objetivo

Permitir consultas em linguagem natural sobre:

1. **Regras de GURPS 4e** (conteúdo estático dos 4 PDFs em `books/`) — para arbitragem em tempo de jogo.
2. **Estado do jogo** (fichas, campanhas, mensagens, saves, assets) — para uma **IA interna futura** acessar tudo que existe no banco.

Exemplo 1: *"Qual a penalidade de Parry após All-Out Attack?"* → retorna trecho do Basic Set: Campaigns com referência de página.

Exemplo 2: *"Quais ataques o Dai Blackthorn usou na última sessão?"* → retorna mensagens e snapshots relevantes da campanha, respeitando permissão.

---

## Decisões fechadas

### 2026-04-21 — revisão: tudo local para eliminar custo recorrente

O híbrido original previa OpenAI pros PDFs. Como a conta OpenAI do usuário estava sem crédito e ele não queria investir nesse processo, migramos **tudo para embeddings locais**. Quality trade-off (~10-15% abaixo da OpenAI em benchmarks gerais) é aceitável; latência é equivalente após o primeiro load do modelo.

| Item | Decisão |
|---|---|
| Vector store | **pgvector** dentro do Postgres existente (zero serviço novo) |
| Embedding (tudo) | **Local** via `sentence-transformers`, modelo `paraphrase-multilingual-mpnet-base-v2` (768 dims). Um único modelo para PDFs e banco — unifica schema, simplifica código. |
| Síntese de resposta | **Adiada**. V-3 entrega retrieval puro (top-K chunks com refs). Claude API é backlog para quando/se houver orçamento. |
| Atualização DB | **Real-time** via Django signals (`post_save` / `post_delete`) |
| Escopo DB | **Tudo** — Campanha, CharacterSheet, CampanhaAssets, Message, SaveState |
| Reprocessamento | Os 3 PDFs com texto (todos exceto GM Screen, que é só imagem) serão indexados uma vez |

Histórico da decisão original (híbrido OpenAI + local) está preservado no `git log` de `docs/RAG_ARCHITECTURE.md`.

---

## Arquitetura em camadas

```
┌──────────────────────────────────────────────────┐
│  UI (tela do GM) + chat de mesa (comando /rule)  │
└──────────────┬───────────────────────────────────┘
               │ pergunta NL
┌──────────────▼───────────────────────────────────┐
│  /api/rules/query  (Django view)                 │
│  - autentica + identifica escopo de campanha     │
│  - gera embedding da pergunta                    │
│  - busca top-K em rule_chunks  (pgvector)        │
│  - busca top-K em entity_embeddings  (pgvector)  │
│    (com filtro obrigatório de permissão)         │
│  - chama Claude API com top-K + instrução        │
│  - devolve resposta + refs (livro/página, ID)    │
└──────────────┬───────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────┐
│  Postgres + pgvector                             │
│  - rule_chunks (book, page, text, embedding_openai) │
│  - entity_embeddings (content_type, object_id,   │
│    campanha_id, scope, text, embedding_local)    │
└──────────────────────────────────────────────────┘
```

---

## Modelos Django

Nova app: `rag/` (isolada do `gurps/` porque é infraestrutura).

```python
# rag/models.py (esboço — a implementar)
class RuleChunk(models.Model):
    book = models.CharField(...)        # "Basic Set: Characters", etc.
    chapter = models.CharField(null=True)
    section = models.CharField(null=True)
    page_start = models.PositiveIntegerField()
    page_end = models.PositiveIntegerField()
    text = models.TextField()
    tokens = models.PositiveIntegerField()
    embedding = VectorField(dimensions=1536)   # text-embedding-3-small
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [ HnswIndex(...) ]            # pgvector HNSW index

class EntityEmbedding(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # isolamento obrigatório
    campanha = models.ForeignKey('gurps.Campanha', null=True, on_delete=CASCADE)
    scope = models.CharField(choices=[('public', ...), ('campanha', ...), ('gm_only', ...)])

    text = models.TextField()                   # representação textual usada no embedding
    embedding = VectorField(dimensions=384)     # sentence-transformers
    source_hash = models.CharField()            # hash do texto, para detectar mudanças
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('content_type', 'object_id')
        indexes = [ HnswIndex(...) ]
```

### Permissões no retrieval

Toda query em `entity_embeddings` aplica filtro automático:
- Jogador: `campanha_id IN (mesas do usuário) AND scope != 'gm_only'`
- GM: `campanha_id IN (mesas onde é dono) AND scope IN (qualquer)`
- Admin: sem filtro (uso restrito)

Isso vive em um `EntityEmbeddingManager` customizado. Nenhuma view pode pular o filtro.

---

## Pipeline de PDFs (OpenAI)

1. Job/comando management (`python manage.py ingest_books`):
   - Varre `books/*.pdf`
   - Para cada PDF, extrai texto por página (usa `pdftotext`)
   - Chunking: janela de ~500 tokens com overlap 10%, respeitando quebras de parágrafo
   - Preserva metadados: `book`, `page_start`, `page_end`, `section` (detectado por heurística de headers)
   - Chama `client.embeddings.create(model="text-embedding-3-small", input=[chunks])` em batch (até 2048 chunks/request)
   - Persiste em `rule_chunks`
2. Idempotência: hash do chunk → `UPDATE` se existe, `INSERT` se novo. Livros só reprocessam se mudou.

## Pipeline do DB (local)

1. Carrega modelo `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` no startup do Django (singleton). Uma vez só; ~500MB em memória.
2. Signal genérico por modelo:
   ```python
   @receiver(post_save, sender=CharacterSheet)
   def reembed_on_save(sender, instance, **kwargs):
       tasks.reembed_entity.delay(sender, instance.pk)   # async
   ```
3. Task assíncrona (Channels worker ou Celery ou simples `threading` — decidir em V-2):
   - Monta representação textual (`__rag_text__` método no model) — define o que entra no embedding
   - Computa hash. Se igual ao salvo, skip.
   - Gera embedding local, persiste em `entity_embeddings`
4. **Caso especial — Message (chat)**: alta frequência de save. Debounce de ~5s ou micro-batch por campanha para não saturar o worker.

## Representações textuais (`__rag_text__`)

Cada modelo define o que descreve sua essência para busca. Exemplo:
- `CharacterSheet`: nome + atributos formatados + lista de vantagens/desvantagens + skills + background
- `Campanha`: nome + descrição + regras + TL + lista de jogadores
- `Message`: timestamp + autor + conteúdo
- `CampanhaAsset`: nome + descrição

Esses métodos são a "interface" entre o ORM e o RAG; alterá-los muda o que o retrieval encontra.

---

## Plano de etapas (V-0 → V-5)

Cada etapa entrega algo testável. Nenhuma etapa depende de aprovação de site em produção — tudo desenvolvido localmente primeiro.

### V-0.0 — Postgres em dev (histórico)
- **Primeira tentativa** (manhã 2026-04-21): Postgres em dev local — bloqueado pela TI na conta Windows.
- **Segunda rota** (tarde 2026-04-21): dev direto na VM do GCP. Funcionou, mas VM de 4 vCPUs sem GPU é muito lenta pra inferência LLM (1-3 min por query RAG).
- **Rota atual** (noite 2026-04-21): usuário tem WSL2 instalado na máquina local com acesso root. Toda a stack de dev migra pra lá. Windows host roda Ollama nativamente (usa GPU RTX 1000 Ada diretamente).

### Estratégia de desenvolvimento atual: WSL2 + Ollama no host
- **WSL2 (Ubuntu)**: Django + Postgres 16 + pgvector + Python 3.13 + sentence-transformers + pymupdf. Zero dependência de serviço externo.
- **Windows host**: Ollama nativo (instalador oficial). Acessa GPU via CUDA. Escuta em 0.0.0.0:11434 (configurável via `OLLAMA_HOST`).
- **Comunicação**: Django dentro do WSL2 chama `http://$(WINDOWS_HOST_IP):11434/api/generate`. O IP do host Windows visto de dentro do WSL2 está em `/etc/resolv.conf` (nameserver) ou via `ip route | grep default`.
- **Books**: montados via `/mnt/c/Users/.../PROJETO-RPG-online/books` ou copiados pra dentro do WSL2. Acessíveis direto.
- **Comparado ao GCP VM**: mesma pilha lógica, mas inferência cai de minutos pra segundos (3-8 s) graças à GPU.

Passos detalhados pra subir esse ambiente em [`docs/SESSION_STATE.md`](SESSION_STATE.md).

### V-0 — Infraestrutura pgvector
- Instalar extensão pgvector no Postgres local
- Criar app Django `rag`
- Modelos `RuleChunk` e `EntityEmbedding` com `pgvector.django.VectorField`
- Migrations
- Instalar deps: `pgvector`, `sentence-transformers`, `openai`
- Sem embeddings ainda — só schema

### V-1 — Ingestão de PDFs (OpenAI)
- Management command `ingest_books`
- Chunking + chamada API + persistência
- Testa com um livro pequeno (GM Screen) primeiro, depois os 4

### V-2 — Pipeline DB (local)
- Singleton do modelo `sentence-transformers`
- Método `__rag_text__` em cada model relevante
- Signals `post_save`/`post_delete` → worker async
- Backfill command `reembed_all` para popular entidades existentes

### V-3 — Endpoint de query (retrieval puro)
- View `POST /api/rules/query` recebe `{question, campanha_id?}`
- Filtro de permissão obrigatório
- Busca top-K em ambos os índices
- Retorna chunks crus com refs (ainda sem síntese)

### V-4 — Síntese via Claude
- Adiciona camada que chama Claude API com os top-K + instrução estruturada
- Usa prompt caching (conteúdo das regras em cache) — reduz custo de queries repetidas
- Retorna resposta em linguagem natural + array de refs citadas

### V-5 — UI
- Tela simples pro GM consultar (htmx?)
- Depois: comando `/rule <pergunta>` integrado ao chat da mesa

### Paralelamente
- Catálogo GURPS estruturado continua (advantages D-Z, disadvantages, skills, etc.) — não bloqueia nem é bloqueado pelo RAG.

---

## Custos estimados

| Item | Ordem de grandeza |
|---|---|
| Embedding inicial 4 PDFs | ~400 pág × ~500 tokens = 200k tokens × $0.02/1M = **~$0.004** |
| Embedding dev DB inicial | Desprezível (volume baixo) |
| Re-embedding em produção | Uma fração por mês — sob $1 salvo eventos massivos |
| Síntese Claude por query | ~$0.001–0.01 por query dependendo do modelo/chunks |
| Modelo local (sentence-transformers) | Gratuito; custo é CPU/RAM na VM |

Embeddings OpenAI estão entre os endpoints mais baratos. **Limite de custo real vai ser queries Claude**, controlável por rate limit.

---

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| VM atual pode não ter RAM para sentence-transformers (~500MB modelo + tokenizer) | Validar RAM disponível antes de V-2. Se faltar, upgrade da VM ou modelo menor (`all-MiniLM-L6-v2`, ~100MB). |
| Chat gera volume alto de embeddings | Debounce 5s ou micro-batch por campanha. |
| Falha de OpenAI bloqueia consulta de regras | Cache de queries frequentes; retrieval sem síntese como fallback. |
| Embedding de DB vaza info entre mesas | `EntityEmbeddingManager` com filtro obrigatório; testes automatizados. |
| Mudança de schema de models requebra representações `__rag_text__` | Tests + backfill command. |
| Hashes de chunks divergem com versão do tokenizer | Versionar o hash junto com model_id do embedding. |
