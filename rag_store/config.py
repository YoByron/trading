from __future__ import annotations

import os
from pathlib import Path

# Root directory for all RAG assets
RAG_ROOT = Path(os.getenv("SENTIMENT_RAG_ROOT", "data/rag")).resolve()

# SQLite database file for structured sentiment snapshots
SQLITE_PATH = RAG_ROOT / "sentiment.db"

# Persistent directory for Chroma vector store
VECTOR_PATH = RAG_ROOT / "vector_store"

# Default embedding model for sentence-transformers
EMBEDDING_MODEL = os.getenv(
    "SENTIMENT_EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

# Directory containing SQL migrations
MIGRATIONS_PATH = Path(__file__).parent / "migrations"


def ensure_directories() -> None:
    """Ensure required directories exist."""
    RAG_ROOT.mkdir(parents=True, exist_ok=True)
    VECTOR_PATH.mkdir(parents=True, exist_ok=True)

