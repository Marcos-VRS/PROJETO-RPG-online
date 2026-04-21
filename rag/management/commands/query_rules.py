"""
CLI para consulta do RAG.

Por default, retorna uma resposta sintetizada pelo LLM local (Ollama), com
citações das páginas. Use --raw para ver apenas os chunks recuperados,
sem síntese.

Exemplos:
    python manage.py query_rules "qual o custo da Visão Aguçada?"
    python manage.py query_rules "penalidade de Parry depois de All-Out Attack"
    python manage.py query_rules "como funciona magia" --book Campaigns --top-k 3
    python manage.py query_rules "skill Broadsword" --raw      # só retrieval
    python manage.py query_rules "..." --raw --full            # raw sem truncar
"""
from django.core.management.base import BaseCommand

import sys

from rag.query import search_rules
from rag.synthesis import DEFAULT_MODEL, synthesize_stream

EXCERPT_CHARS = 600


class Command(BaseCommand):
    help = "Consulta semântica sobre os livros GURPS com resposta sintetizada."

    def add_arguments(self, parser):
        parser.add_argument("question", type=str, help="Pergunta em linguagem natural.")
        parser.add_argument(
            "--top-k",
            type=int,
            default=5,
            help="Quantos chunks alimentar no sintetizador / retornar em raw (default: 5).",
        )
        parser.add_argument(
            "--book",
            type=str,
            default=None,
            help="Filtra por substring do nome do livro (ex.: Campaigns).",
        )
        parser.add_argument(
            "--raw",
            action="store_true",
            help="Não chama LLM; devolve chunks crus com similaridade e página.",
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="No modo --raw, imprime o texto completo de cada chunk (sem truncar).",
        )
        parser.add_argument(
            "--model",
            type=str,
            default=DEFAULT_MODEL,
            help=f"Modelo do Ollama para síntese (default: {DEFAULT_MODEL}).",
        )

    def handle(self, *args, question, top_k, book, raw, full, model, **opts):
        hits = search_rules(question, top_k=top_k, book=book)

        self.stdout.write(self.style.NOTICE(f"\nPergunta: {question}"))
        if book:
            self.stdout.write(self.style.NOTICE(f"Filtro livro ~ {book}"))
        self.stdout.write(f"Chunks encontrados: {len(hits)}")

        if not hits:
            self.stdout.write(self.style.WARNING("  (sem correspondências)"))
            return

        if raw:
            for i, hit in enumerate(hits, 1):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n[{i}] {hit.book}  p.{hit.page_start}"
                        f"  (similaridade={hit.similarity:.3f})"
                    )
                )
                if full or len(hit.text) <= EXCERPT_CHARS:
                    self.stdout.write(hit.text)
                else:
                    self.stdout.write(hit.text[:EXCERPT_CHARS] + "\n  [...truncado]")
            return

        self.stdout.write(self.style.NOTICE(
            "\n>>> Gerando resposta (streaming; primeira chamada carrega o "
            "modelo em RAM e pode levar 1-3 min):\n"
        ))
        # Print each token as it arrives so the user gets immediate feedback.
        for piece in synthesize_stream(question, hits, model=model):
            sys.stdout.write(piece)
            sys.stdout.flush()
        sys.stdout.write("\n")

        self.stdout.write(self.style.NOTICE("\n--- fontes ---"))
        for i, hit in enumerate(hits, 1):
            self.stdout.write(
                f"[{i}] {hit.book}, p.{hit.page_start}  (similaridade={hit.similarity:.3f})"
            )
