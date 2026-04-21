"""
Management command: ingest GURPS PDFs into the RuleChunk vector store.

Pipeline:
  1. Collect PDFs from `books/` directory (or a single --book path).
  2. For each PDF, extract text page by page via `pdftotext` (poppler-utils).
  3. One chunk per non-empty page (V-1 MVP — smarter chunking later).
  4. Deduplicate by (book, text_hash) to stay idempotent across re-runs.
  5. Embed new chunks in batches via OpenAI `text-embedding-3-small`.
  6. Persist to `rag.RuleChunk`.

Requires:
  - `pdftotext` and `pdfinfo` binaries (sudo apt install poppler-utils).
  - OPENAI_API_KEY environment variable.
"""
import hashlib
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rag.models import RuleChunk

OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_DIMENSIONS = 1536
EMBED_BATCH_SIZE = 100


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _approx_tokens(text: str) -> int:
    """Rough token count: 1 token ~= 4 chars for English. Good enough for V-1."""
    return max(1, len(text) // 4)


def _pdf_page_count(pdf: Path) -> int:
    out = subprocess.run(
        ["pdfinfo", str(pdf)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    for line in out.splitlines():
        if line.lower().startswith("pages:"):
            return int(line.split(":", 1)[1].strip())
    raise CommandError(f"Could not determine page count for {pdf}")


def _extract_page_text(pdf: Path, page: int) -> str:
    result = subprocess.run(
        [
            "pdftotext",
            "-f", str(page),
            "-l", str(page),
            "-layout",
            str(pdf),
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _book_title(pdf: Path) -> str:
    # V-1: use filename stem as book identifier.
    # Can be normalized/renamed later without losing data (text_hash is the dedup key).
    return pdf.stem


class Command(BaseCommand):
    help = "Ingest GURPS PDFs into the RuleChunk vector store."

    def add_arguments(self, parser):
        parser.add_argument(
            "--book",
            type=str,
            default=None,
            help="Path to a single PDF. If omitted, scans books/ directory.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Extract and chunk without calling OpenAI or persisting.",
        )
        parser.add_argument(
            "--books-dir",
            type=str,
            default=None,
            help="Directory with PDFs (default: <BASE_DIR>/books).",
        )

    def handle(self, *args, **opts):
        pdfs = self._collect_pdfs(opts["book"], opts["books_dir"])
        client = None
        if not opts["dry_run"]:
            # Lazy import so dry-run works even without openai configured.
            from openai import OpenAI

            client = OpenAI()  # uses OPENAI_API_KEY env var

        grand_total = 0
        for pdf in pdfs:
            self.stdout.write(self.style.NOTICE(f"\n=== {pdf.name} ==="))
            count = self._ingest_pdf(pdf, client, dry_run=opts["dry_run"])
            grand_total += count

        self.stdout.write(
            self.style.SUCCESS(f"\nTotal new chunks embedded: {grand_total}")
        )

    def _collect_pdfs(self, single, books_dir):
        if single:
            p = Path(single)
            if not p.exists():
                raise CommandError(f"{p} does not exist")
            return [p]
        base = Path(books_dir) if books_dir else Path(settings.BASE_DIR) / "books"
        if not base.exists():
            raise CommandError(
                f"{base} does not exist. Put PDFs there or pass --book / --books-dir."
            )
        pdfs = sorted(base.glob("*.pdf"))
        if not pdfs:
            raise CommandError(f"No PDFs found in {base}")
        return pdfs

    def _ingest_pdf(self, pdf, client, *, dry_run):
        book = _book_title(pdf)
        total_pages = _pdf_page_count(pdf)
        self.stdout.write(f"  pages: {total_pages}")

        pending = []  # chunks to embed + persist
        skipped_existing = 0
        skipped_empty = 0

        for page in range(1, total_pages + 1):
            text = _extract_page_text(pdf, page)
            if not text.strip():
                skipped_empty += 1
                continue
            h = _sha256(text)
            if RuleChunk.objects.filter(book=book, text_hash=h).exists():
                skipped_existing += 1
                continue
            pending.append(
                {
                    "book": book,
                    "chapter": "",
                    "section": "",
                    "page_start": page,
                    "page_end": page,
                    "text": text,
                    "tokens": _approx_tokens(text),
                    "text_hash": h,
                }
            )

        self.stdout.write(
            f"  new: {len(pending)} | skipped existing: {skipped_existing} | empty: {skipped_empty}"
        )

        if not pending:
            return 0

        if dry_run:
            self.stdout.write(self.style.WARNING("  [dry-run] skipping embeddings"))
            return 0

        # Embed in batches; OpenAI API accepts up to 2048 inputs per call,
        # but 100 keeps memory and error surface small.
        embedded = 0
        for i in range(0, len(pending), EMBED_BATCH_SIZE):
            batch = pending[i : i + EMBED_BATCH_SIZE]
            self.stdout.write(f"  embedding {i + 1}-{i + len(batch)}...")
            resp = client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=[c["text"] for c in batch],
            )
            for chunk, datum in zip(batch, resp.data):
                RuleChunk.objects.create(
                    **chunk,
                    embedding=datum.embedding,
                    embedding_model=OPENAI_EMBEDDING_MODEL,
                )
                embedded += 1

        self.stdout.write(self.style.SUCCESS(f"  done: {embedded} chunks"))
        return embedded
