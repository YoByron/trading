#!/usr/bin/env python3
"""
Unified RAG System (Dec 2025 Standards)

Uses ChromaDB for vector storage with proper embedding models.
Consolidates lessons learned, sentiment, and trading knowledge.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available. Install with: pip install chromadb")


class UnifiedRAG:
    """
    Modern RAG system using ChromaDB (2025 standards).

    Features:
    - Persistent ChromaDB storage
    - Sentence-transformers embeddings (all-MiniLM-L6-v2)
    - Metadata filtering
    - Multi-collection support (lessons, sentiment, knowledge)
    """

    def __init__(self, persist_directory: str = "data/rag/chroma_db"):
        if not CHROMA_AVAILABLE:
            raise RuntimeError("ChromaDB not installed. Run: pip install chromadb")

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory), settings=Settings(anonymized_telemetry=False)
        )

        # Use modern embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Get or create collections
        self.lessons_collection = self.client.get_or_create_collection(
            name="lessons_learned",
            embedding_function=self.embedding_fn,
            metadata={"description": "Trading lessons learned and mistakes"},
        )

        self.knowledge_collection = self.client.get_or_create_collection(
            name="trading_knowledge",
            embedding_function=self.embedding_fn,
            metadata={"description": "General trading knowledge and strategies"},
        )

        logger.info(f"Initialized UnifiedRAG with ChromaDB at {self.persist_directory}")
        logger.info(f"Lessons collection: {self.lessons_collection.count()} documents")
        logger.info(f"Knowledge collection: {self.knowledge_collection.count()} documents")

    def ingest_lesson(self, lesson_id: str, content: str, metadata: Optional[dict] = None) -> None:
        """Ingest a lesson learned document."""
        try:
            # Clean metadata - ChromaDB only accepts scalar values
            clean_metadata = {}
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, list):
                        # Convert lists to comma-separated strings
                        clean_metadata[key] = ", ".join(str(v) for v in value if v)
                    elif isinstance(value, (str, int, float, bool)):
                        clean_metadata[key] = value
                    elif value is None:
                        continue
                    else:
                        clean_metadata[key] = str(value)

            self.lessons_collection.upsert(
                ids=[lesson_id], documents=[content], metadatas=[clean_metadata]
            )
            logger.info(f"Ingested lesson: {lesson_id}")
        except Exception as e:
            logger.error(f"Failed to ingest lesson {lesson_id}: {e}")

    def query_lessons(
        self, query: str, n_results: int = 5, filter_metadata: Optional[dict] = None
    ) -> dict:
        """
        Query lessons learned.

        Args:
            query: Natural language query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {"severity": "critical"})

        Returns:
            Dict with documents, metadatas, and distances
        """
        try:
            results = self.lessons_collection.query(
                query_texts=[query], n_results=n_results, where=filter_metadata
            )

            logger.info(f"Query '{query}' returned {len(results['documents'][0])} results")
            return results

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_all_lessons_summary(self) -> str:
        """Get a summary of all lessons learned."""
        try:
            count = self.lessons_collection.count()
            if count == 0:
                return "No lessons learned yet."

            # Get all lessons (limited to 100)
            results = self.lessons_collection.get(limit=100)

            # Extract metadata
            severities = {}
            categories = {}

            for metadata in results.get("metadatas", []):
                if metadata:
                    sev = metadata.get("severity", "unknown")
                    cat = metadata.get("category", "unknown")
                    severities[sev] = severities.get(sev, 0) + 1
                    categories[cat] = categories.get(cat, 0) + 1

            summary = f"Total lessons: {count}\n\n"

            if severities:
                summary += "By severity:\n"
                for sev, cnt in sorted(severities.items(), key=lambda x: x[1], reverse=True):
                    summary += f"  - {sev}: {cnt}\n"

            if categories:
                summary += "\nBy category:\n"
                for cat, cnt in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                    summary += f"  - {cat}: {cnt}\n"

            return summary

        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            return f"Error getting summary: {e}"

    def search_by_category(self, category: str, limit: int = 10) -> list[dict]:
        """Get lessons by category."""
        try:
            results = self.lessons_collection.get(where={"category": category}, limit=limit)

            lessons = []
            for i, doc in enumerate(results.get("documents", [])):
                lessons.append(
                    {
                        "id": results["ids"][i] if "ids" in results else f"lesson_{i}",
                        "content": doc,
                        "metadata": results["metadatas"][i] if "metadatas" in results else {},
                    }
                )

            return lessons

        except Exception as e:
            logger.error(f"Failed to search by category {category}: {e}")
            return []


def migrate_old_lessons_to_chroma():
    """Migrate old JSON-based lessons to ChromaDB."""
    import json
    from pathlib import Path

    old_json = Path("data/rag/lessons_learned.json")
    if not old_json.exists():
        print("No old lessons to migrate")
        return

    print(f"Migrating lessons from {old_json}")

    rag = UnifiedRAG()

    try:
        data = json.loads(old_json.read_text())

        for doc in data:
            lesson_id = doc.get("id", doc.get("metadata", {}).get("id", "unknown"))
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            if content:
                rag.ingest_lesson(lesson_id, content, metadata)
                print(f"  ✅ Migrated: {lesson_id}")

        print(f"\n✅ Migration complete! {rag.lessons_collection.count()} lessons in ChromaDB")

    except Exception as e:
        print(f"❌ Migration failed: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Unified RAG System Demo")
    print("=" * 60)
    print()

    # Migrate old lessons
    migrate_old_lessons_to_chroma()

    print()
    print("=" * 60)
    print("Testing Queries")
    print("=" * 60)
    print()

    rag = UnifiedRAG()

    # Test query
    query = "what lessons have we learned about trading"
    print(f"Query: {query}")
    print()

    results = rag.query_lessons(query, n_results=3)

    for i, doc in enumerate(results["documents"][0], 1):
        print(f"{i}. {doc[:200]}...")
        if results["metadatas"][0][i - 1]:
            print(f"   Metadata: {results['metadatas'][0][i - 1]}")
        print()

    # Get summary
    print("=" * 60)
    print("Lessons Summary")
    print("=" * 60)
    print()
    print(rag.get_all_lessons_summary())
