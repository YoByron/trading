"""
ChromaDB Vector Database Client for Trading RAG System

Provides persistent vector storage for market news, sentiment, and research.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.utils.pydantic_compat import ensure_pydantic_base_settings

logger = logging.getLogger(__name__)

ensure_pydantic_base_settings()

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
except Exception as exc:  # noqa: BLE001
    chromadb = None  # type: ignore
    Settings = None  # type: ignore
    logger.warning("ChromaDB import failed - RAG persistence disabled: %s", exc)


class TradingRAGDatabase:
    """
    Persistent vector database for trading system using ChromaDB.

    Features:
    - Persistent storage (survives restarts)
    - Metadata filtering (ticker, date, source)
    - Similarity search with configurable top-k
    - Document management (add, query, delete)
    """

    def __init__(self, persist_directory: str = "data/rag/chroma_db"):
        """
        Initialize ChromaDB client with persistent storage.

        Args:
            persist_directory: Path to store ChromaDB data
        """
        self.persist_directory = persist_directory

        if chromadb is None:
            raise RuntimeError(
                "ChromaDB is not available. Install dependencies or disable the RAG pipeline."
            )

        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection for market news
        self.collection = self.client.get_or_create_collection(
            name="market_news",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )

        logger.info(f"ChromaDB initialized at {persist_directory}")
        logger.info(f"Collection 'market_news' has {self.collection.count()} documents")

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add documents to the vector database.

        Args:
            documents: List of text content to embed
            metadatas: List of metadata dicts (ticker, date, source, etc.)
            ids: Optional list of unique IDs (auto-generated if None)

        Returns:
            Dict with status and count

        Example:
            db.add_documents(
                documents=["NVDA beats earnings...", "GOOGL announces..."],
                metadatas=[
                    {"ticker": "NVDA", "date": "2025-11-10", "source": "yahoo"},
                    {"ticker": "GOOGL", "date": "2025-11-10", "source": "bloomberg"}
                ]
            )
        """
        if not documents:
            return {"status": "error", "message": "No documents provided"}

        if len(documents) != len(metadatas):
            return {"status": "error", "message": "Documents and metadatas length mismatch"}

        # Auto-generate IDs if not provided
        if ids is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ids = [f"doc_{timestamp}_{i}" for i in range(len(documents))]

        try:
            # Add to ChromaDB (will automatically generate embeddings)
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Added {len(documents)} documents to RAG database")
            return {
                "status": "success",
                "count": len(documents),
                "ids": ids
            }

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return {"status": "error", "message": str(e)}

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the vector database with semantic search.

        Args:
            query_text: Natural language query
            n_results: Number of results to return (default 5)
            where: Metadata filters (e.g., {"ticker": "NVDA"})

        Returns:
            Dict with documents, metadatas, distances, ids

        Example:
            # Get recent NVDA news
            results = db.query(
                query_text="NVIDIA earnings and revenue growth",
                n_results=10,
                where={"ticker": "NVDA"}
            )
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )

            return {
                "status": "success",
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }

        except Exception as e:
            logger.error(f"Error querying database: {e}")
            return {"status": "error", "message": str(e)}

    def get_ticker_news(
        self,
        ticker: str,
        n_results: int = 20,
        date_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all news for a specific ticker.

        Args:
            ticker: Stock ticker (e.g., "NVDA")
            n_results: Max results to return
            date_filter: Optional date filter (YYYY-MM-DD)

        Returns:
            List of news articles with content and metadata
        """
        where = {"ticker": ticker}
        if date_filter:
            where["date"] = date_filter

        # Query with ticker-specific prompt
        results = self.query(
            query_text=f"Latest news and analysis for {ticker}",
            n_results=n_results,
            where=where
        )

        if results["status"] != "success":
            return []

        # Combine into article objects
        articles = []
        for i in range(len(results["documents"])):
            articles.append({
                "content": results["documents"][i],
                "metadata": results["metadatas"][i],
                "relevance_score": 1 - results["distances"][i],  # Convert distance to similarity
                "id": results["ids"][i]
            })

        return articles

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID.

        Args:
            doc_id: Document ID

        Returns:
            Document dict or None if not found
        """
        try:
            result = self.collection.get(ids=[doc_id])

            if not result["documents"]:
                return None

            return {
                "content": result["documents"][0],
                "metadata": result["metadatas"][0],
                "id": result["ids"][0]
            }

        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None

    def delete_by_id(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    def count(self) -> int:
        """Get total number of documents in database."""
        return self.collection.count()

    def reset(self) -> bool:
        """
        Delete all documents from the collection.

        WARNING: This is irreversible!

        Returns:
            True if successful
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection("market_news")
            self.collection = self.client.get_or_create_collection(
                name="market_news",
                metadata={"hnsw:space": "cosine"}
            )
            logger.warning("RAG database reset - all documents deleted")
            return True

        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dict with total documents, unique tickers, date range, etc.
        """
        try:
            total_docs = self.collection.count()

            # Get all metadata to compute stats
            if total_docs == 0:
                return {
                    "total_documents": 0,
                    "unique_tickers": 0,
                    "sources": [],
                    "date_range": None
                }

            # Sample up to 1000 documents for stats
            sample_size = min(total_docs, 1000)
            results = self.collection.get(limit=sample_size)

            metadatas = results["metadatas"]

            # Extract unique tickers and sources
            tickers = set(m.get("ticker") for m in metadatas if m.get("ticker"))
            sources = set(m.get("source") for m in metadatas if m.get("source"))
            dates = [m.get("date") for m in metadatas if m.get("date")]

            date_range = None
            if dates:
                dates.sort()
                date_range = {"start": dates[0], "end": dates[-1]}

            return {
                "total_documents": total_docs,
                "unique_tickers": len(tickers),
                "tickers": sorted(list(tickers)),
                "sources": sorted(list(sources)),
                "date_range": date_range,
                "sample_size": sample_size
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}


# Convenience function for quick access
def get_rag_db(persist_directory: str = "data/rag/chroma_db") -> TradingRAGDatabase:
    """
    Get or create a RAG database instance.

    Args:
        persist_directory: Path to ChromaDB storage

    Returns:
        TradingRAGDatabase instance
    """
    return TradingRAGDatabase(persist_directory=persist_directory)
