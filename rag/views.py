"""
HTTP views for RAG.

- `query_page`: renderiza a página HTML de consulta.
- `query_api`:  endpoint POST que recebe {question, top_k?, book?} e
                devolve uma resposta em streaming NDJSON.

O Django runserver/daphne mantém o processo vivo, então o modelo de
embedding (sentence-transformers) é carregado UMA VEZ e reusado em todas
as queries. Só isso já remove ~5s por chamada.
"""
import json

from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from rag.query import search_rules
from rag.synthesis import DEFAULT_MODEL, synthesize_stream


def query_page(request):
    """Simple HTML form for manual testing."""
    return render(request, "rag/query.html", {"default_model": DEFAULT_MODEL})


@csrf_exempt  # dev-only; adicionar proteção CSRF + auth antes de ir pra prod
@require_http_methods(["POST"])
def query_api(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid JSON body")

    question = (body.get("question") or "").strip()
    if not question:
        return HttpResponseBadRequest("missing 'question'")

    top_k = int(body.get("top_k") or 5)
    book = body.get("book") or None
    model = body.get("model") or DEFAULT_MODEL

    hits = search_rules(question, top_k=top_k, book=book)

    def stream():
        # 1) metadata com as fontes (antes do LLM gerar qualquer coisa)
        yield json.dumps(
            {
                "sources": [
                    {
                        "book": h.book,
                        "page_start": h.page_start,
                        "page_end": h.page_end,
                        "similarity": round(h.similarity, 3),
                    }
                    for h in hits
                ]
            },
            ensure_ascii=False,
        ) + "\n"

        # 2) tokens da síntese conforme chegam do Ollama
        if hits:
            try:
                for piece in synthesize_stream(question, hits, model=model):
                    yield json.dumps({"token": piece}, ensure_ascii=False) + "\n"
            except RuntimeError as exc:
                yield json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n"

        # 3) marcador de fim
        yield json.dumps({"done": True}) + "\n"

    response = StreamingHttpResponse(stream(), content_type="application/x-ndjson")
    response["Cache-Control"] = "no-cache"
    return response
