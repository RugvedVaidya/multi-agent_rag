"""
retriever.py — Hybrid search + re-ranking
Embeddings: ChromaDB built-in (ONNX, no TensorFlow dependency)
"""

import math
import re
from collections import Counter
import chromadb
from chromadb.utils import embedding_functions
import config

# Use ChromaDB's built-in ONNX embedding function — no sentence-transformers needed
_ef = embedding_functions.DefaultEmbeddingFunction()


def embed_query(text: str) -> list[float]:
    return _ef([text])[0]


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def bm25_score(query_tokens, doc, avg_dl=200, k1=1.5, b=0.75):
    doc_tokens = tokenize(doc)
    dl         = len(doc_tokens)
    tf_map     = Counter(doc_tokens)
    score      = 0.0
    for term in query_tokens:
        tf      = tf_map.get(term, 0)
        idf     = math.log(1.5 + 0.5)
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avg_dl, 1)))
        score  += idf * tf_norm
    return score


def retrieve(query: str, top_k=config.TOP_K_RETRIEVAL,
             rerank_k=config.TOP_K_RERANK) -> list[dict]:
    db         = chromadb.PersistentClient(path=config.CHROMA_DIR)
    collection = db.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs       = results["documents"][0]
    metas      = results["metadatas"][0]
    distances  = results["distances"][0]
    sem_scores = [1 - d for d in distances]

    query_tokens = tokenize(query)
    avg_dl       = sum(len(tokenize(d)) for d in docs) / max(len(docs), 1)

    candidates = []
    for doc, meta, sem in zip(docs, metas, sem_scores):
        if sem < config.SIMILARITY_THRESH:
            continue
        kw    = min(bm25_score(query_tokens, doc, avg_dl) / 10.0, 1.0)
        final = 0.7 * sem + 0.3 * kw
        candidates.append({
            "text":           doc,
            "source":         meta.get("source", ""),
            "file_name":      meta.get("file_name", ""),
            "chunk_index":    meta.get("chunk_index", 0),
            "file_type":      meta.get("file_type", ""),
            "semantic_score": round(sem, 4),
            "keyword_score":  round(kw, 4),
            "final_score":    round(final, 4),
        })

    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    return candidates[:rerank_k]


def format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant context found."
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Source {i}: {c['file_name']} | chunk {c['chunk_index']} "
            f"| score {c['final_score']}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)