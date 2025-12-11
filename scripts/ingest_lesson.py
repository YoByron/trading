import logging
from datetime import datetime
from pathlib import Path

from src.rag.vector_db.chroma_client import get_rag_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_lesson():
    db = get_rag_db()
    lesson_path = Path(
        "/Users/ganapolsky_i/workspace/git/igor/trading/rag_knowledge/raw/20251211_lesson_sharpe_ratio.txt"
    )

    if not lesson_path.exists():
        logger.error("Lesson file not found")
        return

    with open(lesson_path) as f:
        content = f.read()

    logger.info("Ingesting lesson...")

    # Create document
    doc = content
    metadata = {
        "ticker": "LESSON_LEARNED",
        "source": "internal_incident",
        "date": "2025-12-11",
        "category": "backtesting",
        "severity": "high",
    }
    doc_id = f"lesson_sharpe_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Add to DB
    result = db.add_documents(documents=[doc], metadatas=[metadata], ids=[doc_id])

    if result["status"] == "success":
        logger.info("✅ Lesson learned ingested successfully")

        # Verify retrieval
        logger.info("Verifying retrieval...")
        results = db.query("Sharpe ratio zero division", n_results=1)
        if results["documents"]:
            logger.info(f"Retrieval verified: {results['documents'][0][:100]}...")
        else:
            logger.warning("Could not retrieve ingested lesson immediately")

    else:
        logger.error(f"Failed to ingest: {result.get('message')}")


if __name__ == "__main__":
    ingest_lesson()
