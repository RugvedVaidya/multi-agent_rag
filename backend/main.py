"""
backend/main.py — FastAPI server for Multi-Agent RAG

Endpoints:
  POST /chat/stream   — SSE stream of pipeline events + final answer
  POST /ingest        — upload and ingest files
  GET  /stats         — DB chunk count and indexed files
  DELETE /reset       — clear the vector DB
"""

import os
import json
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import config
import orchestrator
import chromadb
from ingest import ingest_path, get_collection

app = FastAPI(title="Multi-Agent RAG API", version="1.0.0")

# Allow the Vite dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


# ── SSE helpers ───────────────────────────────────────────────

def sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_pipeline(question: str, history: list[dict]) -> AsyncGenerator[str, None]:
    """
    Run the agent pipeline and yield SSE events at each stage so the
    frontend can animate the pipeline trace in real time.
    """
    # ── Stage 0: route ────────────────────────────────────────
    yield sse("status", {"stage": "routing", "message": "Classifying query…"})
    await asyncio.sleep(0)   # let the event flush

    needs_rag = orchestrator.needs_retrieval(question)

    if not needs_rag:
        yield sse("status", {"stage": "chat", "message": "Direct response (no retrieval needed)"})
        answer = orchestrator.chat_response(question, history)
        yield sse("done", {
            "answer": answer,
            "sources": [],
            "queries_used": [],
            "critic_verdict": "PASS",
            "critic_score": 1.0,
            "pipeline": "chat",
        })
        return

    # ── Stage 1: researcher ───────────────────────────────────
    yield sse("status", {"stage": "researcher", "message": "Rewriting query…"})
    await asyncio.sleep(0)

    from agents import researcher, analyst, critic

    research = researcher.run(question, history)
    yield sse("researcher_done", {
        "queries": research["queries"],
        "chunks_found": len(research["chunks"]),
        "sources": research["source_files"],
    })
    await asyncio.sleep(0)

    if not research["chunks"]:
        yield sse("done", {
            "answer": "I couldn't find relevant information in the knowledge base. "
                      "Please upload and ingest relevant documents first.",
            "sources": [],
            "queries_used": research["queries"],
            "critic_verdict": "PASS",
            "critic_score": 0.0,
            "pipeline": "rag",
        })
        return

    # ── Stage 2: analyst ──────────────────────────────────────
    yield sse("status", {"stage": "analyst", "message": "Synthesizing answer…"})
    await asyncio.sleep(0)

    analyst_result = analyst.run(
        question=question,
        context=research["context"],
        history=history,
    )
    yield sse("analyst_done", {"model": analyst_result["model_used"]})
    await asyncio.sleep(0)

    # ── Stage 3: critic ───────────────────────────────────────
    yield sse("status", {"stage": "critic", "message": "Verifying answer…"})
    await asyncio.sleep(0)

    critic_result = critic.run(
        question=question,
        answer=analyst_result["answer"],
        context=research["context"],
    )
    yield sse("critic_done", {
        "verdict": critic_result["verdict"],
        "score": critic_result["score"],
        "issues": critic_result.get("issues", []),
    })
    await asyncio.sleep(0)

    # ── Final answer ──────────────────────────────────────────
    yield sse("done", {
        "answer": critic_result["final_answer"],
        "sources": research["source_files"],
        "queries_used": research["queries"],
        "critic_verdict": critic_result["verdict"],
        "critic_score": critic_result["score"],
        "pipeline": "rag",
    })


# ── Routes ────────────────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    return StreamingResponse(
        stream_pipeline(req.question, history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/ingest")
async def ingest_files(files: list[UploadFile] = File(...)):
    """Accept uploaded files, save to temp dir, and ingest them."""
    ingested = []
    errors   = []

    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            ext  = Path(f.filename).suffix.lower()
            dest = os.path.join(tmp, f.filename)
            try:
                content = await f.read()
                with open(dest, "wb") as out:
                    out.write(content)
                ingested.append(f.filename)
            except Exception as e:
                errors.append({"file": f.filename, "error": str(e)})

        if ingested:
            ingest_path(tmp)

    col = get_collection()
    return {
        "ingested": ingested,
        "errors":   errors,
        "total_chunks": col.count(),
    }


@app.get("/stats")
async def stats():
    """Return current DB stats."""
    try:
        col    = get_collection()
        count  = col.count()
        # Get unique file names from metadata
        result = col.get(include=["metadatas"], limit=10000)
        files  = list({m.get("file_name", "") for m in result["metadatas"] if m.get("file_name")})
        return {"chunk_count": count, "files": files}
    except Exception as e:
        return {"chunk_count": 0, "files": [], "error": str(e)}


@app.delete("/reset")
async def reset_db():
    """Clear the entire vector database."""
    try:
        db  = chromadb.PersistentClient(path=config.CHROMA_DIR)
        db.delete_collection(config.COLLECTION_NAME)
        return {"message": "Knowledge base cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}