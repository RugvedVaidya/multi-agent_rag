"""
ingest.py — Load → Chunk → Embed → Store
Embeddings: ChromaDB built-in ONNX (no TensorFlow/sentence-transformers)
"""

import sys
import hashlib
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from rich.console import Console

import config

console = Console()
_ef     = embedding_functions.DefaultEmbeddingFunction()
STORE_BATCH = 50


def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _chunks_from_text(text: str, source: str, start_idx: int = 0):
    size    = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP
    words   = text.split()
    idx     = start_idx
    pos     = 0
    while pos < len(words):
        yield {
            "text":        " ".join(words[pos : pos + size]),
            "source":      source,
            "chunk_index": idx,
        }
        idx += 1
        pos += size - overlap


def _store_batch(collection, batch, fhash, fname, ext):
    texts      = [c["text"] for c in batch]
    embeddings = _ef(texts)
    ids        = [f"{fhash}_{c['chunk_index']}" for c in batch]
    metadatas  = [{
        "source":      c["source"],
        "chunk_index": c["chunk_index"],
        "file_hash":   fhash,
        "file_name":   fname,
        "file_type":   ext,
    } for c in batch]
    collection.add(ids=ids, embeddings=embeddings,
                   documents=texts, metadatas=metadatas)


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
        console.print(f"[yellow]Skipped[/yellow]: {fname}")
        return 0

    fhash    = file_hash(path)
    existing = collection.get(where={"file_hash": fhash}, limit=1)
    if existing["ids"]:
        console.print(f"[dim]Already ingested:[/dim] {fname}")
        return 0

    console.print(f"[cyan]Ingesting:[/cyan] {fname}")
    total, batch, chunk_idx = 0, [], 0

    def flush():
        nonlocal total, batch
        if batch:
            _store_batch(collection, batch, fhash, fname, ext)
            total += len(batch)
            batch.clear()

    if ext == ".pdf":
        reader  = PdfReader(path)
        n_pages = len(reader.pages)
        console.print(f"  → {n_pages} pages...")
        for pn, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if not text.strip():
                continue
            for chunk in _chunks_from_text(text, path, chunk_idx):
                batch.append(chunk); chunk_idx += 1
                if len(batch) >= STORE_BATCH:
                    flush()
                    console.print(f"  [dim]stored {total} chunks (page {pn+1}/{n_pages})[/dim]")
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if not text.strip():
            return 0
        for chunk in _chunks_from_text(text, path):
            batch.append(chunk); chunk_idx += 1
            if len(batch) >= STORE_BATCH:
                flush()

    flush()
    if total == 0:
        console.print(f"[yellow]No text extracted:[/yellow] {fname}")
        return 0
    console.print(f"  [green]✓[/green] {total} chunks stored")
    return total


def ingest_path(path: str):
    collection = get_collection()
    total      = 0
    p          = Path(path)

    if p.is_file():
        total += ingest_file(str(p), collection)
    elif p.is_dir():
        files = [f for f in p.rglob("*")
                 if f.is_file() and f.suffix.lower() in config.SUPPORTED_EXTENSIONS]
        console.print(f"\n[bold]Found {len(files)} files[/bold]")
        for f in files:
            total += ingest_file(str(f), collection)
    else:
        console.print(f"[red]Not found:[/red] {path}")
        return

    console.print(f"\n[bold green]Done![/bold green] Total chunks: {collection.count()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <file_or_folder>")
        sys.exit(1)
    ingest_path(sys.argv[1])