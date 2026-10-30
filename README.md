# industrial-doc-assistant

A retrieval-augmented generation (RAG) assistant for workshop safety. It answers questions in French using only a corpus of public Suva documents (machine-tool safety, metalworking) and cites its sources as document and page. If the documents do not contain the answer, it says so.

> **Status:** work in progress. Ingestion is complete; retrieval, answer generation, UI and evaluation are in progress.

## Architecture

```
PDF ──► extraction ──► chunking ──► embeddings ──► Azure AI Search index
        (per page)    (300 words,   (Azure OpenAI)  (keywords + vectors)
                       50 overlap)

question ──► embedding ──► hybrid search ──► top 5 chunks ──► chat model ──► answer + sources
```

## Stack

- Python, `pypdf`, `openai`, `azure-search-documents`
- Azure OpenAI via Microsoft Foundry: `text-embedding-3-small` (1536 dimensions), `gpt-5.4-mini`
- Azure AI Search: French analyzer for keywords, HNSW index for vectors
- Streamlit (planned)

## Getting started

Requires Python 3.10+, an Azure OpenAI resource with an embedding and a chat deployment, and an Azure AI Search service.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                 # fill in your Azure endpoints, keys and deployment names
```

Place the source PDFs in `data/raw/` (not versioned), then build the index:

```powershell
python scripts/ingest.py
```

The ingestion is idempotent: chunk IDs are deterministic, so re-running it updates documents instead of duplicating them. Secrets stay in `.env`, which is ignored by Git.

## Project structure

```
src/docassistant/   configuration, Azure clients, ingestion
scripts/            entry points (ingestion, connection checks)
data/raw/           source PDFs (not versioned)
eval/               evaluation set and results
```

## Roadmap

- [x] Azure setup and connection checks
- [x] Ingestion pipeline (extraction, chunking, embeddings, index)
- [ ] Hybrid retrieval and answer generation with citations
- [ ] Streamlit interface
- [ ] Evaluation (accuracy, source correctness, hallucinations, out-of-scope questions)
- [ ] CI (ruff, pytest)

## Limitations

- Text extraction only: diagrams and images are not indexed.
- Fixed-size chunks that ignore document structure, so tables are extracted as flat text.
- Page citations use the PDF page index, which can differ from printed page numbers.

## License

MIT. The Suva documents remain the property of their authors.
