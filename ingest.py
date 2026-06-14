"""
ingest.py  —  Load → Chunk → Embed → Store

Embeddings: local sentence-transformers (free, no API key needed)
Streams large files in batches to avoid MemoryError.
Run:  python ingest.py <path_to_file_or_folder>
"""

import sys
import hashlib
from pathlib import Path

import chromadb
from pypdf import PdfReader
from rich.console import Console
from sentence_transformers import SentenceTransformer

import config

console = Console()

# Load local embedding model once (downloads ~90MB on first run)
console.print("[dim]Loading embedding model...[/dim]")
_embedder = SentenceTransformer(config.EMBEDDING_MODEL)
console.print("[dim]Embedding model ready.[/dim]")

STORE_BATCH = 50   # chunks per embed+store cycle


# ── Helpers ───────────────────────────────────────────────────

def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _chunks_from_text(text: str, source: str, start_idx: int = 0):
    """
    Generator: yield overlapping fixed-size word-based chunks.
    Uses words instead of tokens to avoid tiktoken/memory issues.
    """
    size    = config.CHUNK_SIZE      # words per chunk
    overlap = config.CHUNK_OVERLAP   # word overlap
    words   = text.split()
    idx     = start_idx
    pos     = 0

    while pos < len(words):
        chunk_words = words[pos : pos + size]
        yield {
            "text":        " ".join(chunk_words),
            "source":      source,
            "chunk_index": idx,
        }
        idx += 1
        pos += size - overlap

    
def _embed(texts: list[str]) -> list[list[float]]:
    """Embed texts locally using sentence-transformers."""
    embeddings = _embedder.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def _store_batch(collection, batch: list[dict], fhash: str, fname: str, ext: str):
    texts      = [c["text"] for c in batch]
    embeddings = _embed(texts)
    ids        = [f"{fhash}_{c['chunk_index']}" for c in batch]
    metadatas  = [
        {
            "source":      c["source"],
            "chunk_index": c["chunk_index"],
            "file_hash":   fhash,
            "file_name":   fname,
            "file_type":   ext,
        }
        for c in batch
    ]
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


# ── Main ingestion logic ───────────────────────────────────────

def get_collection():
    db = chromadb.PersistentClient(path=config.CHROMA_DIR)
    return db.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_file(path: str, collection) -> int:
    path  = str(Path(path).resolve())
    ext   = Path(path).suffix.lower()
    fname = Path(path).name

    if ext not in config.SUPPORTED_EXTENSIONS:
        console.print(f"[yellow]Skipped[/yellow] (unsupported type): {fname}")
        return 0

    fhash    = file_hash(path)
    existing = collection.get(where={"file_hash": fhash}, limit=1)
    if existing["ids"]:
        console.print(f"[dim]Already ingested:[/dim] {fname}")
        return 0

    console.print(f"[cyan]Ingesting:[/cyan] {fname}")

    total_chunks = 0
    batch: list[dict] = []
    chunk_idx = 0

    def flush():
        nonlocal total_chunks, batch
        if batch:
            _store_batch(collection, batch, fhash, fname, ext)
            total_chunks += len(batch)
            batch = []

    if ext == ".pdf":
        reader  = PdfReader(path)
        n_pages = len(reader.pages)
        console.print(f"  → {n_pages} pages...")

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                continue
            for chunk in _chunks_from_text(page_text, path, chunk_idx):
                batch.append(chunk)
                chunk_idx += 1
                if len(batch) >= STORE_BATCH:
                    flush()
                    console.print(f"  [dim]stored {total_chunks} chunks (page {page_num+1}/{n_pages})[/dim]")
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if not text.strip():
            console.print(f"[yellow]Empty, skipped:[/yellow] {fname}")
            return 0
        for chunk in _chunks_from_text(text, path):
            batch.append(chunk)
            chunk_idx += 1
            if len(batch) >= STORE_BATCH:
                flush()

    flush()   # remaining chunks

    if total_chunks == 0:
        console.print(f"[yellow]No text extracted from:[/yellow] {fname}")
        return 0

    console.print(f"  [green]✓[/green] {total_chunks} chunks stored")
    return total_chunks


def ingest_path(path: str):
    collection   = get_collection()
    total_chunks = 0
    p            = Path(path)

    if p.is_file():
        total_chunks += ingest_file(str(p), collection)
    elif p.is_dir():
        files = [
            f for f in p.rglob("*")
            if f.is_file() and f.suffix.lower() in config.SUPPORTED_EXTENSIONS
        ]
        console.print(f"\n[bold]Found {len(files)} files in {path}[/bold]\n")
        for f in files:
            total_chunks += ingest_file(str(f), collection)
    else:
        console.print(f"[red]Path not found:[/red] {path}")
        return

    console.print(f"\n[bold green]Done![/bold green] Total chunks in DB: {collection.count()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[red]Usage:[/red] python ingest.py <file_or_folder>")
        sys.exit(1)
    ingest_path(sys.argv[1])