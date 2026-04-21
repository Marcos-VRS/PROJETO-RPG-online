"""
CLI wrapper para busca semântica em RuleChunk.

Exemplo:
    python manage.py query_rules "penalidade de Parry apos All-Out Attack"
    python manage.py query_rules "como funciona a magia" --book Campaigns --top-k 3
    python manage.py query_rules "skill Broadsword" --full
"""
from django.core.management.base import BaseCommand

from rag.query import search_rules

EXCERPT_CHARS = 600


class Command(BaseCommand):
    help = "Semantic search over ingested GURPS rule chunks."

    def add_arguments(self, parser):
        parser.add_argument("question", type=str, help="Pergunta em linguagem natural.")
        parser.add_argument(
            "--top-k",
            type=int,
            default=5,
            help="Quantos resultados retornar (default: 5).",
        )
        parser.add_argument(
            "--book",
            type=str,
            default=None,
            help="Filtra por substring do nome do livro (ex.: Campaigns).",
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="Imprime o texto completo de cada chunk, em vez de excerto.",
        )

    def handle(self, *args, question, top_k, book, full, **opts):
        hits = search_rules(question, top_k=top_k, book=book)

        self.stdout.write(self.style.NOTICE(f"\nQuery: {question}"))
        if book:
            self.stdout.write(self.style.NOTICE(f"Filter book ~ {book}"))
        self.stdout.write(f"Results: {len(hits)}\n")

        if not hits:
            self.stdout.write(self.style.WARNING("  (no matches)"))
            return

        for i, hit in enumerate(hits, 1):
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n[{i}] {hit.book}  p.{hit.page_start}"
                    f"  (similarity={hit.similarity:.3f})"
                )
            )
            if full or len(hit.text) <= EXCERPT_CHARS:
                self.stdout.write(hit.text)
            else:
                self.stdout.write(hit.text[:EXCERPT_CHARS] + "\n  [...truncated]")
