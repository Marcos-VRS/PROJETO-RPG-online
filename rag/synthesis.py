"""
Local LLM synthesis via Ollama.

Takes a question plus the top-K retrieved RuleHits and produces a direct,
grounded answer in Portuguese with page references. All inference is local.

Endpoint: http://localhost:11434/api/generate (Ollama default).
Model:    qwen2.5:7b-instruct (multilingual, ~4.7GB, CPU-friendly).
"""
import json
import urllib.error
import urllib.request
from typing import Iterator

OLLAMA_URL = "http://localhost:11434/api/generate"
# Default: 3b é bem mais rápido em CPU sem perder muito em qualidade PT-BR.
# Para melhor qualidade em trade de velocidade: qwen2.5:7b-instruct.
DEFAULT_MODEL = "qwen2.5:3b-instruct"
DEFAULT_TIMEOUT = 600  # seconds — CPU inference is slow; big margin on first call

SYSTEM_PROMPT = """\
Você é um assistente especialista em GURPS 4ª Edição.
Sua tarefa é responder a pergunta do usuário SOMENTE com base nos trechos fornecidos dos livros.

REGRAS:
- Seja direto. No primeiro parágrafo, dê a resposta objetiva.
- SEMPRE cite a fonte entre colchetes no formato [Nome do livro, p.N] logo após cada afirmação.
- Se a resposta não estiver nos trechos, responda exatamente: "Não encontrei essa regra nos trechos disponíveis."
- NÃO invente, NÃO extrapole, NÃO adicione informação que não esteja nos trechos.
- Termine oferecendo aprofundamento: "Quer que eu detalhe X ou Y?"
- Responda em português do Brasil.
"""


def _build_prompt(question: str, hits) -> str:
    context = "\n\n".join(
        f"[Trecho {i + 1}] {h.book}, p.{h.page_start}\n{h.text}"
        for i, h in enumerate(hits)
    )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== TRECHOS DOS LIVROS ===\n{context}\n\n"
        f"=== PERGUNTA ===\n{question}\n\n"
        f"=== RESPOSTA ===\n"
    )


def _request_body(question, hits, model, temperature, stream):
    return {
        "model": model,
        "prompt": _build_prompt(question, hits),
        "stream": stream,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_ctx": 4096,
            "num_predict": 500,  # cap output length
        },
    }


def _open_ollama(req, timeout):
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Não consegui conectar no Ollama em {OLLAMA_URL}. "
            f"Verifique se o serviço está rodando (`systemctl status ollama`). "
            f"Detalhe: {exc}"
        ) from exc


def synthesize(
    question: str,
    hits,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Non-streaming: retorna a resposta completa quando termina."""
    if not hits:
        return "Não encontrei trechos relevantes para essa pergunta."

    body = _request_body(question, hits, model, temperature, stream=False)
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with _open_ollama(req, timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return (payload.get("response") or "").strip()


def synthesize_stream(
    question: str,
    hits,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    timeout: int = DEFAULT_TIMEOUT,
) -> Iterator[str]:
    """Streaming: yielda fragmentos conforme o modelo os gera.

    Consumidores devem imprimir cada chunk assim que chegar pra UX imediato.
    Encerra naturalmente quando `done: true` vier no JSON de controle.
    """
    if not hits:
        yield "Não encontrei trechos relevantes para essa pergunta."
        return

    body = _request_body(question, hits, model, temperature, stream=True)
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with _open_ollama(req, timeout) as resp:
        for raw_line in resp:
            if not raw_line:
                continue
            try:
                obj = json.loads(raw_line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            piece = obj.get("response", "")
            if piece:
                yield piece
            if obj.get("done"):
                break
