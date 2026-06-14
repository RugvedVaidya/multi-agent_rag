import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")

# ── LLM settings (Groq — free tier, OpenAI-compatible) ────────
GROQ_BASE_URL     = "https://api.groq.com/openai/v1"
AGENT_MODEL       = "llama-3.3-70b-versatile"
STRONG_MODEL      = "llama-3.3-70b-versatile"

# ── Embeddings (local, fully free via sentence-transformers) ───
# No API key needed — runs on your CPU
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"

# ── Chunking ──────────────────────────────────────────────────
CHUNK_SIZE        = 512
CHUNK_OVERLAP     = 64

# ── Retrieval ─────────────────────────────────────────────────
TOP_K_RETRIEVAL   = 4
TOP_K_RERANK      = 4
SIMILARITY_THRESH = 0.0

# ── Vector DB ─────────────────────────────────────────────────
CHROMA_DIR        = "./chroma_db"
COLLECTION_NAME   = "knowledge_base"

# ── Supported file types ───────────────────────────────────────
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".py", ".js", ".ts",
                        ".java", ".cpp", ".c", ".go", ".rs", ".html", ".css"}