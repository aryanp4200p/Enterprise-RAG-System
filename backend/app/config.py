"""Central configuration. Every value can be overridden with an environment variable."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # the backend/ folder

DATA_DIR = Path(os.getenv("RAG_DATA_DIR", BASE_DIR / "data"))
CHROMA_DIR = Path(os.getenv("RAG_CHROMA_DIR", BASE_DIR / "chroma_db"))

EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv("RAG_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "llama-3.3-70b-versatile")

CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

# candidates fetched from each retriever, and chunks kept after reranking
RETRIEVAL_K = int(os.getenv("RAG_RETRIEVAL_K", "5"))
RERANK_TOP_K = int(os.getenv("RAG_RERANK_TOP_K", "4"))

MAX_QUERY_CHARS = int(os.getenv("RAG_MAX_QUERY_CHARS", "2000"))

# Comma separated list of allowed browser origins, e.g.
#   CORS_ORIGINS=https://my-app.vercel.app,http://localhost:5173
# "*" allows every origin (fine for a demo, lock it down for production).
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

# Load the models when the server starts instead of on the first request.
WARMUP = os.getenv("RAG_WARMUP", "false").lower() in {"1", "true", "yes"}
