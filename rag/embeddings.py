"""
Local embedding helper using sentence-transformers.

One multilingual model serves both the RuleChunk (PDFs) and EntityEmbedding
(DB content) paths — same dimension (768), unified vector math, zero external
API cost.

The model is lazily loaded the first time `embed_texts` is called and cached
as a module-level singleton so subsequent calls reuse it. First call on a
fresh checkout downloads the weights (~280MB) from HuggingFace into
`~/.cache/huggingface/`.
"""
from functools import lru_cache
from typing import Iterable

EMBEDDING_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIMENSIONS = 768


@lru_cache(maxsize=1)
def get_model():
    """Return the shared SentenceTransformer instance (loaded on first call)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    """Embed a list of strings. Returns list of Python float lists (pgvector-compatible)."""
    texts = list(texts)
    if not texts:
        return []
    model = get_model()
    vectors = model.encode(
        texts,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,  # cosine similarity ready
    )
    return [v.tolist() for v in vectors]
