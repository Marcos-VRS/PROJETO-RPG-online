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
from typing import Iterable

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:7b-instruct"
DEFAULT_TIMEOUT = 180  # seconds — CPU inference is slow

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


def synthesize(
    question: str,
    hits,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Call Ollama to produce a grounded answer from `hits`."""
    if not hits:
        return "Não encontrei trechos relevantes para essa pergunta."

    prompt = _build_prompt(question, hits)
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_ctx": 4096,
        },
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Não consegui conectar no Ollama em {OLLAMA_URL}. "
            f"Verifique se `ollama serve` está rodando. Detalhe: {exc}"
        ) from exc

    return (payload.get("response") or "").strip()
