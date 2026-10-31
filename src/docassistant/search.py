"""Retrieval: find the passages that best match a question in the Azure AI Search index.

Three modes, so they can be compared in the evaluation:
  - "hybrid"  keywords + vectors, fused by Azure AI Search (RRF). Default, used by the app.
  - "keyword" keyword search only (BM25 with the French analyzer).
  - "vector"  vector similarity only.
"""
from dataclasses import dataclass

from azure.search.documents.models import VectorizedQuery

from .clients import search_client
from .ingest import embed

MODES = ("hybrid", "keyword", "vector")
VECTOR_CANDIDATES = 50  # nearest neighbours taken from the vector ranking before fusion


@dataclass(frozen=True)
class Passage:
    source: str
    page: int
    chunk: int
    content: str
    score: float


def retrieve(question: str, top: int = 5, source: str | None = None, mode: str = "hybrid") -> list[Passage]:
    """Return the `top` passages that best match the question."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")

    search_text = question if mode in ("hybrid", "keyword") else None
    vector_queries = None
    if mode in ("hybrid", "vector"):
        vector_queries = [
            VectorizedQuery(
                vector=embed([question])[0],
                k_nearest_neighbors=VECTOR_CANDIDATES,
                fields="content_vector",
            )
        ]

    odata_filter = f"source eq '{source.replace(chr(39), chr(39) * 2)}'" if source else None
    results = search_client().search(
        search_text=search_text,
        vector_queries=vector_queries,
        filter=odata_filter,
        select=["source", "page", "chunk", "content"],
        top=top,
    )
    return [
        Passage(r["source"], r["page"], r["chunk"], r["content"], r["@search.score"])
        for r in results
    ]
