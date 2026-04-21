"""
Diagnostic: medir tempo de chamadas ao Ollama com prompts de tamanhos
diferentes, para isolar se o gargalo é o tamanho do prompt ou o pipeline.

Roda 3 testes em sequência:
  1. Prompt minúsculo (~20 tokens)
  2. Prompt médio (~300 tokens)
  3. Prompt grande (~1500 tokens), similar ao que o RAG manda

Imprime tempo total, primeiro-token-latency e tokens/s.
"""
import json
import time
import urllib.request

from django.core.management.base import BaseCommand

from rag.synthesis import DEFAULT_MODEL, OLLAMA_URL


class Command(BaseCommand):
    help = "Bench Ollama direto (sem RAG) com prompts de tamanhos variados."

    def add_arguments(self, parser):
        parser.add_argument("--model", type=str, default=DEFAULT_MODEL)

    def handle(self, *args, model, **opts):
        cases = [
            ("pequeno (~20 tok)", "Responda em uma frase: o que é GURPS?"),
            (
                "médio (~300 tok)",
                ("GURPS é um sistema de RPG genérico criado por Steve Jackson. "
                 "Os atributos primários são ST DX IQ e HT, cada um custando "
                 "pontos diferentes. Vantagens e desvantagens ajustam o total "
                 "de pontos. Skills são compradas com custo por nível. ") * 5
                + "\n\nResponda: quanto custa Visão Aguçada?",
            ),
            (
                "grande (~1500 tok)",
                ("GURPS é um sistema de RPG genérico criado por Steve Jackson. "
                 "Os atributos primários são ST DX IQ e HT, cada um custando "
                 "pontos diferentes. Vantagens e desvantagens ajustam o total "
                 "de pontos. Skills são compradas com custo por nível. "
                 "Habilidades como Acute Vision custam 2 pontos por nível. "
                 "Ambidexterity custa 5 pontos fixos. Altered Time Rate custa "
                 "100 pontos por nível. Allies variam conforme frequência de "
                 "aparição e poder. ") * 30
                + "\n\nResponda: quanto custa Visão Aguçada?",
            ),
        ]

        self.stdout.write(f"Modelo: {model}\n")
        for label, prompt in cases:
            self.stdout.write(f"\n=== {label} | {len(prompt)} chars ===")
            self._run_bench(prompt, model, stream=False)
            self._run_bench(prompt, model, stream=True)

    def _run_bench(self, prompt, model, *, stream):
        body = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {"num_predict": 80, "num_ctx": 4096},
        }
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        t0 = time.monotonic()
        first_token_at = None
        output_chars = 0

        with urllib.request.urlopen(req, timeout=600) as resp:
            if stream:
                for raw in resp:
                    if not raw.strip():
                        continue
                    try:
                        obj = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    piece = obj.get("response", "")
                    if piece and first_token_at is None:
                        first_token_at = time.monotonic()
                    output_chars += len(piece)
                    if obj.get("done"):
                        break
            else:
                data = json.loads(resp.read().decode("utf-8"))
                output_chars = len(data.get("response", ""))

        total = time.monotonic() - t0
        ttf = f"{first_token_at - t0:.1f}s" if first_token_at else "n/a"
        mode = "stream" if stream else "full  "
        self.stdout.write(
            f"  [{mode}] total={total:6.2f}s  first_token={ttf:>5}  out_chars={output_chars}"
        )
