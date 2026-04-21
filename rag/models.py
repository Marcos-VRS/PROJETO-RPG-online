"""
RAG models.

- `RuleChunk`: trecho de livro de regras (GURPS PDFs), embeddings gerados localmente via sentence-transformers multilingual-mpnet (768 dims).
- `EntityEmbedding`: embedding de uma entidade do banco (ficha, campanha, mensagem),
  gerado pelo mesmo modelo local. Dados privados nunca saem da VM.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from pgvector.django import HnswIndex, VectorField


class RuleChunk(models.Model):
    """Trecho de livro de regras, embeddings gerados localmente via sentence-transformers multilingual-mpnet (768 dims)."""

    book = models.CharField(max_length=200)
    chapter = models.CharField(max_length=200, blank=True)
    section = models.CharField(max_length=500, blank=True)
    page_start = models.PositiveIntegerField()
    page_end = models.PositiveIntegerField()
    text = models.TextField()
    tokens = models.PositiveIntegerField()
    text_hash = models.CharField(max_length=64, db_index=True)
    embedding = VectorField(dimensions=768)
    embedding_model = models.CharField(
        max_length=100, default="paraphrase-multilingual-mpnet-base-v2"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            HnswIndex(
                name="rule_chunk_emb_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            models.Index(fields=["book", "page_start"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["book", "text_hash"],
                name="unique_chunk_per_book",
            ),
        ]

    def __str__(self):
        return f"{self.book} p.{self.page_start}-{self.page_end}"


class EntityEmbedding(models.Model):
    """Embedding local (sentence-transformers multilingual-mpnet, 768 dims) de qualquer model do banco.

    Vinculado via GenericForeignKey para cobrir Campanha, CharacterSheet, Message, etc.
    `campanha` e `scope` implementam o isolamento obrigatório entre mesas.
    Usa o mesmo modelo e dimensão que RuleChunk para simplificar e permitir queries cruzadas.
    """

    SCOPE_CHOICES = [
        ("public", "Público"),
        ("campanha", "Campanha"),
        ("gm_only", "Apenas GM"),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    campanha = models.ForeignKey(
        "gurps.Campanha",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="rag_embeddings",
    )
    scope = models.CharField(
        max_length=20, choices=SCOPE_CHOICES, default="campanha"
    )

    text = models.TextField()
    text_hash = models.CharField(max_length=64, db_index=True)
    embedding = VectorField(dimensions=768)
    embedding_model = models.CharField(
        max_length=100,
        default="paraphrase-multilingual-mpnet-base-v2",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            HnswIndex(
                name="entity_emb_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["campanha", "scope"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="unique_embedding_per_entity",
            ),
        ]

    def __str__(self):
        return f"{self.content_type} #{self.object_id}"
