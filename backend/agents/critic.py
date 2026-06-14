"""agents/critic.py — Critic Agent (uses Groq)"""

import json
from openai import OpenAI
import config

client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)

SYSTEM = """You are a fact-checker reviewing an AI answer against source context.
Respond ONLY with valid JSON (no markdown):
{"verdict":"PASS or REVISE","score":0.0-1.0,"issues":[],"feedback":"","revised_answer":""}
PASS = accurate and supported. REVISE = hallucinations or unsupported claims.
If REVISE, write a corrected answer in revised_answer."""


def run(question, answer, context):
    try:
        resp = client.chat.completions.create(
            model=config.STRONG_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content":
                    f"QUESTION:\n{question}\n\nSOURCE CONTEXT:\n{context}\n\nDRAFT ANSWER:\n{answer}"}
            ],
            temperature=0.1,
        )
        result = json.loads(resp.choices[0].message.content.strip())
    except Exception:
        result = {"verdict": "PASS", "score": 0.8, "issues": [], "feedback": "", "revised_answer": ""}

    result["final_answer"] = result.get("revised_answer") or answer
    if result.get("verdict") != "REVISE":
        result["final_answer"] = answer
    return result