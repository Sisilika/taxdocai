"""
RAG layer: a small Chroma vector store seeded with chunks of IRS form
instructions (e.g. W-2 box 12 codes, 1099-NEC vs 1099-MISC guidance).

In this scaffold the corpus is a handful of hand-written reference chunks
(see knowledge_seed.py) so the project runs with zero external downloads.
To extend: drop real IRS instruction PDFs into /sample_docs/irs_instructions/
and run `python -m app.rag.ingest` to chunk + embed them instead.
"""
import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_store")

_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Free local embedding model (no API key needed) so RAG works even without
# an Anthropic key configured yet.
_embedder = embedding_functions.DefaultEmbeddingFunction()

_collection = _client.get_or_create_collection(
    name="irs_instructions",
    embedding_function=_embedder,
)


def seed_if_empty():
    if _collection.count() > 0:
        return
    from app.rag.knowledge_seed import SEED_CHUNKS
    _collection.add(
        documents=[c["text"] for c in SEED_CHUNKS],
        metadatas=[{"source": c["source"]} for c in SEED_CHUNKS],
        ids=[c["id"] for c in SEED_CHUNKS],
    )


def query_knowledge(question: str, n_results: int = 3) -> list[dict]:
    seed_if_empty()
    results = _collection.query(query_texts=[question], n_results=n_results)
    out = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        out.append({"text": doc, "source": meta.get("source"), "distance": dist})
    return out
