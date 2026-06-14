"""agents/researcher.py — Researcher Agent (uses Groq)"""

import json
from openai import OpenAI
import config
from retriever import retrieve, format_context

client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)

REWRITE_SYSTEM = """You are a search query optimizer.
Rewrite the user question into 1-3 precise search queries for a document knowledge base.
Respond ONLY with valid JSON (no markdown, no preamble):
{"queries": ["query 1", "query 2"]}
Rules: expand abbreviations, focus on key concepts. Simple question = 1 query."""


def rewrite_query(question, history):
    history_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history[-3:])
    user_msg = f"History:\n{history_text}\n\nQuestion: {question}" if history_text else f"Question: {question}"
    try:
        resp = client.chat.completions.create(
            model=config.AGENT_MODEL,
            messages=[{"role": "system", "content": REWRITE_SYSTEM},
                      {"role": "user",   "content": user_msg}],
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content.strip())
        return [q for q in data.get("queries", [question]) if q.strip()] or [question]
    except Exception:
        return [question]


def run(question, history=None):
    history = history or []
    queries = rewrite_query(question, history)

    seen, all_chunks = set(), []
    for q in queries:
        for chunk in retrieve(q):
            key = (chunk["source"], chunk["chunk_index"])
            if key not in seen:
                seen.add(key)
                all_chunks.append(chunk)

    all_chunks.sort(key=lambda x: x["final_score"], reverse=True)
    top = all_chunks[:config.TOP_K_RERANK]

    return {
        "queries":      queries,
        "chunks":       top,
        "context":      format_context(top),
        "source_files": list({c["file_name"] for c in top}),
    }