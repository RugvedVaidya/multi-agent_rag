"""agents/analyst.py — Analyst Agent (uses Groq)"""

from openai import OpenAI
import config

client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)

SYSTEM = """You are a precise research analyst. Answer questions using ONLY the
provided source context. Cite sources inline as [Source N]. If context is
insufficient, say so. Never fabricate information."""


def run(question, context, history=None):
    history = history or []
    messages = [{"role": "system", "content": SYSTEM}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history[-4:]]
    messages.append({"role": "user", "content":
        f"Context:\n\n{context}\n\n---\n\nQuestion: {question}\n\n"
        "Answer using ONLY the context above, with [Source N] citations."})

    resp = client.chat.completions.create(
        model=config.AGENT_MODEL, messages=messages, temperature=0.3)
    return {"answer": resp.choices[0].message.content.strip(), "model_used": config.AGENT_MODEL}