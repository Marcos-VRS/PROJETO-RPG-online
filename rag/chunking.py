"""
Text chunking for RAG ingestion.

Strategy (V-2):
  - Split a page's text into paragraphs (double-newline separated).
  - Greedy-merge small paragraphs until hitting `target_tokens`.
  - Split any paragraph bigger than `max_tokens` at sentence boundaries.
  - Each emitted chunk fits between `min_tokens` and `max_tokens`.

Token count is the same cheap heuristic used everywhere else
(`len(text) // 4`). Precise tokenization is not needed — we only want
chunks that fit the embedding model's context and are topic-coherent.
"""
import re
from typing import Iterator

MIN_TOKENS = 50
TARGET_TOKENS = 300
MAX_TOKENS = 500

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý])")


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _split_paragraphs(text: str) -> list[str]:
    """Split on blank lines, trim, drop empties."""
    raw = re.split(r"\n\s*\n", text)
    return [p.strip() for p in raw if p.strip()]


def _split_sentences(paragraph: str) -> list[str]:
    """Naive sentence splitter. Sufficient for English and PT-BR prose in GURPS."""
    parts = _SENTENCE_SPLIT_RE.split(paragraph.strip())
    return [s.strip() for s in parts if s.strip()]


def chunk_page(
    text: str,
    *,
    min_tokens: int = MIN_TOKENS,
    target_tokens: int = TARGET_TOKENS,
    max_tokens: int = MAX_TOKENS,
) -> list[str]:
    """Split a page's text into coherent chunks sized near `target_tokens`.

    - If the page is smaller than `max_tokens`, returns one chunk.
    - Otherwise merges paragraphs up to `target_tokens`, flushing when adding
      the next paragraph would exceed `max_tokens`.
    - A single paragraph exceeding `max_tokens` gets split at sentence
      boundaries.
    """
    text = text.strip()
    if not text:
        return []
    if _approx_tokens(text) <= max_tokens:
        return [text]

    paragraphs = _split_paragraphs(text)
    # A page with no blank-line breaks but still too large: treat as one paragraph.
    if len(paragraphs) <= 1:
        paragraphs = [text]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    def flush():
        nonlocal current_parts, current_tokens
        if current_parts:
            chunks.append("\n\n".join(current_parts).strip())
            current_parts = []
            current_tokens = 0

    for para in paragraphs:
        para_tokens = _approx_tokens(para)

        if para_tokens > max_tokens:
            flush()
            for sentence_chunk in _split_oversize_paragraph(
                para, target_tokens, max_tokens
            ):
                chunks.append(sentence_chunk)
            continue

        if current_tokens and current_tokens + para_tokens > max_tokens:
            flush()

        current_parts.append(para)
        current_tokens += para_tokens

        if current_tokens >= target_tokens:
            flush()

    flush()

    # Merge any chunk below min_tokens into its neighbor (except if it's alone).
    return _merge_tiny_chunks(chunks, min_tokens, max_tokens)


def _split_oversize_paragraph(
    paragraph: str, target_tokens: int, max_tokens: int
) -> Iterator[str]:
    """Split a huge paragraph at sentence boundaries into chunks ~target_tokens."""
    sentences = _split_sentences(paragraph)
    if not sentences:
        # Fallback: hard-split by character count.
        step = target_tokens * 4
        for i in range(0, len(paragraph), step):
            yield paragraph[i : i + step]
        return

    current: list[str] = []
    current_tokens = 0
    for s in sentences:
        s_tokens = _approx_tokens(s)
        if current_tokens and current_tokens + s_tokens > max_tokens:
            yield " ".join(current).strip()
            current = []
            current_tokens = 0
        current.append(s)
        current_tokens += s_tokens
        if current_tokens >= target_tokens:
            yield " ".join(current).strip()
            current = []
            current_tokens = 0
    if current:
        yield " ".join(current).strip()


def _merge_tiny_chunks(
    chunks: list[str], min_tokens: int, max_tokens: int
) -> list[str]:
    """Merge a chunk shorter than `min_tokens` into the previous one if the
    combined length still fits under `max_tokens`."""
    if len(chunks) <= 1:
        return chunks
    out: list[str] = [chunks[0]]
    for c in chunks[1:]:
        if _approx_tokens(c) < min_tokens:
            combined = out[-1] + "\n\n" + c
            if _approx_tokens(combined) <= max_tokens:
                out[-1] = combined
                continue
        out.append(c)
    return out
