"""
RAG (Retrieval-Augmented Generation) System for Trading

Provides:
- Vector database storage (ChromaDB)
- Embedding generation (sentence-transformers)
- Semantic search and retrieval
- News ingestion pipeline
"""

from .config import get_config, validate_config

__version__ = "1.0.0"

try:  # Optional Chromadb-backed components
    from .vector_db import ChromaClient, Embedder, Retriever  # type: ignore  # noqa: F401

    __all__ = [
        "ChromaClient",
        "Embedder",
        "Retriever",
        "get_config",
        "validate_config",
    ]
except Exception:  # pragma: no cover - chromadb not installed
    __all__ = [
        "get_config",
        "validate_config",
    ]
