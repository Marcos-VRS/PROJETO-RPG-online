"""
Management command: ingest GURPS PDFs into the RuleChunk vector store.

Pipeline:
  1. Collect PDFs from `books/` directory (or a single --book path).
  2. Extract text page by page via pymupdf (fitz).
  3. Paragraph-aware chunking (see `rag.chunking.chunk_page`): one page
     may yield several chunks, each between 50 and 500 "tokens" (approx).
  4. Deduplicate by (book, text_hash) to stay idempotent across re-runs.
  5. Embed new chunks locally via `rag.embeddings.embed_texts`
     (sentence-transformers multilingual, 768 dims).
  6. Persist to `rag.RuleChunk`.

Flags:
  --book PATH       ingest a single PDF
  --books-dir PATH  override books directory
  --dry-run         extract + chunk without embedding/persisting
  --reset           delete existing chunks of the same book(s) before ingesting
"""
import hashlib
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from rag.chunking import chunk_page
from rag.embeddings import EMBEDDING_MODEL_NAME, embed_texts
from rag.models import RuleChunk

EMBED_BATCH_SIZE = 32
MIN_CHUNK_CHARS = 20


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _book_title(pdf: Path) -> str:
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
            help="Extract and chunk without embedding or persisting.",
        )
        parser.add_argument(
            "--books-dir",
            type=str,
            default=None,
            help="Directory with PDFs (default: <BASE_DIR>/books).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing chunks for the targeted book(s) before ingesting.",
        )

    def handle(self, *args, **opts):
        import fitz  # noqa: F401

        pdfs = self._collect_pdfs(opts["book"], opts["books_dir"])

        if opts["reset"]:
            for pdf in pdfs:
                book = _book_title(pdf)
                deleted, _ = RuleChunk.objects.filter(book=book).delete()
                self.stdout.write(
                    self.style.WARNING(f"  [reset] deleted {deleted} existing chunks for {book}")
                )

        grand_total = 0
        for pdf in pdfs:
            self.stdout.write(self.style.NOTICE(f"\n=== {pdf.name} ==="))
            count = self._ingest_pdf(pdf, dry_run=opts["dry_run"])
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

    def _ingest_pdf(self, pdf, *, dry_run):
        import fitz

        book = _book_title(pdf)
        doc = fitz.open(pdf)
        try:
            total_pages = len(doc)
            self.stdout.write(f"  pages: {total_pages}")

            pending = []
            skipped_existing = 0
            skipped_empty = 0
            skipped_tiny = 0

            for page_num in range(total_pages):
                raw = doc[page_num].get_text().strip()
                if not raw:
                    skipped_empty += 1
                    continue
                for chunk_text in chunk_page(raw):
                    if len(chunk_text) < MIN_CHUNK_CHARS:
                        skipped_tiny += 1
                        continue
                    h = _sha256(chunk_text)
                    if RuleChunk.objects.filter(book=book, text_hash=h).exists():
                        skipped_existing += 1
                        continue
                    pending.append(
                        {
                            "book": book,
                            "chapter": "",
                            "section": "",
                            "page_start": page_num + 1,
                            "page_end": page_num + 1,
                            "text": chunk_text,
                            "tokens": _approx_tokens(chunk_text),
                            "text_hash": h,
                        }
                    )
        finally:
            doc.close()

        self.stdout.write(
            f"  new: {len(pending)} | skipped: existing={skipped_existing} "
            f"empty={skipped_empty} tiny={skipped_tiny}"
        )

        if not pending:
            return 0

        if dry_run:
            self.stdout.write(self.style.WARNING("  [dry-run] skipping embeddings"))
            return 0

        embedded = 0
        for i in range(0, len(pending), EMBED_BATCH_SIZE):
            batch = pending[i : i + EMBED_BATCH_SIZE]
            page_range = f"p.{batch[0]['page_start']}-{batch[-1]['page_end']}"
            self.stdout.write(f"  batch {i + 1}-{i + len(batch)} ({page_range})...")
            vectors = embed_texts([c["text"] for c in batch])
            with transaction.atomic():
                for chunk, vec in zip(batch, vectors):
                    RuleChunk.objects.create(
                        **chunk,
                        embedding=vec,
                        embedding_model=EMBEDDING_MODEL_NAME,
                    )
                    embedded += 1

        self.stdout.write(self.style.SUCCESS(f"  done: {embedded} chunks"))
        return embedded
