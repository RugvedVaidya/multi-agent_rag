"""orchestrator.py — Pipeline Orchestrator (uses Groq)"""

from openai import OpenAI
from rich.console import Console

import config
from agents import researcher, analyst, critic

client  = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)
console = Console()

ROUTER_SYSTEM = """Decide if this question needs document retrieval.
Reply with ONE word only: RETRIEVE or CHAT
RETRIEVE: asks about facts, documents, data, or specific information
CHAT: greeting, small talk, or question about the assistant itself"""


def needs_retrieval(question):
    resp = client.chat.completions.create(
        model=config.AGENT_MODEL,
        messages=[{"role": "system", "content": ROUTER_SYSTEM},
                  {"role": "user",   "content": question}],
        max_tokens=5, temperature=0.0,
    )
    return "RETRIEVE" in resp.choices[0].message.content.strip().upper()


def chat_response(question, history):
    messages = [{"role": "system", "content": "You are a helpful research assistant. Be concise."},
                *history[-4:],
                {"role": "user", "content": question}]
    resp = client.chat.completions.create(model=config.AGENT_MODEL, messages=messages, temperature=0.7)
    return resp.choices[0].message.content.strip()


def run(question, history=None, verbose=False):
    history = history or []
    trace   = {}

    if not needs_retrieval(question):
        if verbose: console.print("[dim]Route: CHAT[/dim]")
        return {"answer": chat_response(question, history), "sources": [],
                "queries_used": [], "critic_score": 1.0,
                "critic_verdict": "PASS", "pipeline": "chat", "trace": {}}

    if verbose: console.print("[dim]Route: RAG pipeline[/dim]")

    # Stage 1: Researcher
    if verbose: console.print("[cyan]→ Researcher agent...[/cyan]")
    res = researcher.run(question, history)
    trace["researcher"] = {"queries": res["queries"], "chunks": len(res["chunks"])}
    if verbose: console.print(f"  Queries: {res['queries']} | Chunks: {len(res['chunks'])}")

    if not res["chunks"]:
        return {"answer": "I couldn't find relevant information in the knowledge base. "
                          "Please ingest relevant documents first.",
                "sources": [], "queries_used": res["queries"],
                "critic_score": 0.0, "critic_verdict": "PASS",
                "pipeline": "rag", "trace": trace}

    # Stage 2: Analyst
    if verbose: console.print("[cyan]→ Analyst agent...[/cyan]")
    ana = analyst.run(question=question, context=res["context"], history=history)
    trace["analyst"] = {"model": ana["model_used"]}

    # Stage 3: Critic
    if verbose: console.print("[cyan]→ Critic agent...[/cyan]")
    crit = critic.run(question=question, answer=ana["answer"], context=res["context"])
    trace["critic"] = {"verdict": crit["verdict"], "score": crit["score"]}

    if verbose:
        color = "green" if crit["verdict"] == "PASS" else "yellow"
        console.print(f"  [{color}]{crit['verdict']}[/{color}] | score: {crit['score']}")
        for issue in crit.get("issues", []):
            console.print(f"  [yellow]Issue:[/yellow] {issue}")

    return {
        "answer":         crit["final_answer"],
        "sources":        res["source_files"],
        "queries_used":   res["queries"],
        "critic_score":   crit["score"],
        "critic_verdict": crit["verdict"],
        "pipeline":       "rag",
        "trace":          trace if verbose else {},
    }