"""
Semantic search over the RAG corpus.

Current scope: `RuleChunk` (livros). `EntityEmbedding` (banco) entra quando
V-2 popular dados.

Distance metric: cosine (via pgvector). Embeddings já são normalizados em
`rag.embeddings.embed_texts`, então cosine e inner product dão ordenação
equivalente; `<=>` (cosine) é escolhido pelo bom suporte do pgvector a HNSW.
"""
from dataclasses import dataclass
from typing import Optional

from pgvector.django import CosineDistance

from rag.embeddings import embed_texts
from rag.models import RuleChunk


@dataclass
class RuleHit:
    id: int
    book: str
    page_start: int
    page_end: int
    text: str
    distance: float  # 0 = idêntico, 2 = oposto

    @property
    def similarity(self) -> float:
        """Similaridade cosseno em [-1, 1], maior = mais parecido."""
        return 1 - self.distance


DEFAULT_TOP_K = 3  # balanço entre cobertura e prompt eval speed em CPU


def search_rules(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    book: Optional[str] = None,
) -> list[RuleHit]:
    """Retorna os top-K chunks mais próximos da pergunta.

    `book`: substring case-insensitive para restringir a um livro específico
    (ex.: "Campaigns" filtra só no Basic Set Campaigns).
    """
    if not query or not query.strip():
        return []

    query_vec = embed_texts([query])[0]
    qs = RuleChunk.objects.annotate(
        distance=CosineDistance("embedding", query_vec)
    )
    if book:
        qs = qs.filter(book__icontains=book)
    qs = qs.order_by("distance")[:top_k]

    return [
        RuleHit(
            id=r.id,
            book=r.book,
            page_start=r.page_start,
            page_end=r.page_end,
            text=r.text,
            distance=float(r.distance),
        )
        for r in qs
    ]
