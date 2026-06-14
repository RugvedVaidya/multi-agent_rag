# Multi-Agent RAG Assistant

An advanced Retrieval-Augmented Generation system with a 3-agent pipeline: **Researcher → Analyst → Critic**. Supports PDFs, TXT, Markdown, and code files. Fully free to run using Groq (LLM) and local sentence-transformers (embeddings).

## Architecture

```
User Query
    │
    ▼
Orchestrator  ──── decides: RAG or simple chat
    │
    ▼
Researcher Agent  ──── rewrites query, retrieves relevant chunks (hybrid search)
    │
    ▼
Analyst Agent  ──── synthesizes answer with inline citations
    │
    ▼
Critic Agent  ──── verifies answer against sources, flags hallucinations
    │
    ▼
Final Answer (with faithfulness score)
```

## Features

- **Hybrid search** — semantic (cosine similarity) + BM25 keyword scoring, blended 70/30
- **Query rewriting** — LLM expands and decomposes queries for better retrieval
- **Self-verification** — critic agent checks every answer against source chunks
- **Multi-format ingestion** — PDF, TXT, MD, and most code file types
- **Memory-safe ingestion** — streams large files in batches, no MemoryError on big PDFs
- **Duplicate detection** — SHA-256 file hashing skips already-ingested files
- **Conversation history** — multi-turn awareness across all agents
- **Free to run** — Groq free tier (LLM) + local all-MiniLM-L6-v2 (embeddings)

## Tech Stack

| Component | Tool |
|---|---|
| LLM (agents) | Groq — `llama-3.3-70b-versatile` (free tier) |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` (local, free) |
| Vector DB | ChromaDB (local persistent) |
| PDF parsing | pypdf |
| CLI | Rich |

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/multi_agent_rag.git
cd multi_agent_rag
pip install -r requirements.txt
```

### 2. Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free, no credit card required)
3. Create an API key

### 3. Configure

```bash
cp .env.example .env
# Edit .env and add your Groq key
```

`.env` contents:
```
GROQ_API_KEY=gsk_your_key_here
```

### 4. Run

```bash
python main.py
```

With pipeline trace visible:
```bash
python main.py --verbose
```

Ingest documents at startup:
```bash
python main.py --ingest ./your_documents_folder
```

## Usage

Once running, use these commands inside the chat:

| Command | Description |
|---|---|
| `/ingest <path>` | Add a file or folder to the knowledge base |
| `/stats` | Show how many chunks are indexed |
| `/verbose` | Toggle pipeline trace on/off |
| `/clear` | Clear conversation history |
| `/quit` | Exit |

Then just ask questions about your documents:

```
You: What are the main findings in the report?
You: Summarize the recommendations from chapter 3
You: What does the code in utils.py do?
```

## Project Structure

```
multi_agent_rag/
├── main.py              # CLI entry point
├── orchestrator.py      # Coordinates the agent pipeline
├── ingest.py            # Load → Chunk → Embed → Store
├── retriever.py         # Hybrid search + re-ranking
├── config.py            # Models, chunking, retrieval settings
├── agents/
│   ├── researcher.py    # Query rewriting + retrieval
│   ├── analyst.py       # Answer synthesis with citations
│   └── critic.py        # Hallucination detection + verification
├── requirements.txt
├── .env.example
└── .gitignore
```

## Configuration

All settings are in `config.py`:

```python
CHUNK_SIZE        = 512     # words per chunk
CHUNK_OVERLAP     = 64      # word overlap between chunks
TOP_K_RETRIEVAL   = 8       # chunks retrieved per query
TOP_K_RERANK      = 4       # chunks kept after re-ranking
SIMILARITY_THRESH = 0.0     # minimum similarity score (0.0 = accept all)
```

## Roadmap

- [ ] Streamlit web UI
- [ ] Evaluation harness (retrieval precision + answer faithfulness scoring)
- [ ] Retry loop: critic sends bad answers back to analyst
- [ ] Web search tool for agents
- [ ] Support for DOCX, CSV, and HTML ingestion