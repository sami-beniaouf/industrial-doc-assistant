"""Ingestion: PDFs -> text chunks -> embeddings -> Azure AI Search index.

Run from the repository root:  python -m docassistant.ingest   (with src on PYTHONPATH)
or simply:                     python scripts/ingest.py

Steps
1. Read every PDF in data/raw, page by page (we keep the page number for citations).
2. Split each page into overlapping chunks of about CHUNK_WORDS words.
3. Create the embedding of each chunk, in batches.
4. Create the index if it does not exist, then upload the chunks.
   Chunk IDs are deterministic (file + page + position), so running the script
   again updates the same documents instead of creating duplicates.
"""
import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from openai import RateLimitError
from pypdf import PdfReader

from .clients import openai_client, search_client, search_index_client
from .config import settings

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CHUNK_WORDS = 300       # about one or two paragraphs
OVERLAP_WORDS = 50      # shared words between neighbouring chunks, so an idea cut in two is not lost
EMBED_BATCH = 16


@dataclass
class Chunk:
    id: str
    source: str
    page: int
    chunk: int
    content: str


def read_pdf(path: Path) -> list[tuple[int, str]]:
    """Return (page number, text) for each page that contains text."""
    reader = PdfReader(path)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = " ".join((page.extract_text() or "").split())
        text = re.sub(r"(?<=\w)- (?=[a-zà-ÿ])", "-", text)  # rejoin line-break hyphens: "Machines- outils" -> "Machines-outils"
        if text:
            pages.append((number, text))
    return pages


def split_words(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if len(words) <= size:
        return [text]
    step = size - overlap
    return [" ".join(words[start:start + size]) for start in range(0, len(words) - overlap, step)]


def make_id(source: str, page: int, position: int) -> str:
    # Search keys only accept letters, digits, '_', '-' and '='; a hash keeps them valid and stable.
    return hashlib.sha1(f"{source}|{page}|{position}".encode()).hexdigest()


def build_chunks() -> list[Chunk]:
    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDF found in {RAW_DIR}")
    chunks = []
    for pdf in pdfs:
        pages = read_pdf(pdf)
        before = len(chunks)
        for page_number, text in pages:
            for position, piece in enumerate(split_words(text)):
                chunks.append(Chunk(make_id(pdf.name, page_number, position), pdf.name, page_number, position, piece))
        print(f"{pdf.name}: {len(pages)} pages with text, {len(chunks) - before} chunks")
    return chunks


def embed(texts: list[str]) -> list[list[float]]:
    client = openai_client()
    vectors = []
    for start in range(0, len(texts), EMBED_BATCH):
        batch = texts[start:start + EMBED_BATCH]
        for attempt in range(5):
            try:
                response = client.embeddings.create(model=settings.embedding_deployment, input=batch)
                break
            except RateLimitError:
                wait = 2 ** attempt
                print(f"Rate limit reached, retry in {wait} s")
                time.sleep(wait)
        else:
            raise RuntimeError("Embedding failed after 5 attempts")
        vectors.extend(item.embedding for item in response.data)
        print(f"Embedded {min(start + EMBED_BATCH, len(texts))}/{len(texts)} chunks")
    return vectors


def ensure_index() -> None:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="fr.microsoft"),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="page", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SimpleField(name="chunk", type=SearchFieldDataType.Int32),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=settings.embedding_dimensions,
            vector_search_profile_name="default-profile",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="default-profile", algorithm_configuration_name="hnsw")],
    )
    index = SearchIndex(name=settings.search_index, fields=fields, vector_search=vector_search)
    search_index_client().create_or_update_index(index)
    print(f"Index '{settings.search_index}' ready")


def upload(chunks: list[Chunk], vectors: list[list[float]]) -> None:
    documents = [
        {
            "id": c.id,
            "content": c.content,
            "source": c.source,
            "page": c.page,
            "chunk": c.chunk,
            "content_vector": v,
        }
        for c, v in zip(chunks, vectors)
    ]
    client = search_client()
    for start in range(0, len(documents), 100):
        results = client.merge_or_upload_documents(documents[start:start + 100])
        failed = [r.key for r in results if not r.succeeded]
        if failed:
            raise RuntimeError(f"{len(failed)} documents failed to upload, e.g. {failed[:3]}")
    print(f"Uploaded {len(documents)} chunks")


def main() -> None:
    chunks = build_chunks()
    vectors = embed([c.content for c in chunks])
    ensure_index()
    upload(chunks, vectors)


if __name__ == "__main__":
    main()
