#!/usr/bin/env python3
"""
Ingest Lesson Learned into RAG.

Usage:
    python3 scripts/ingest_lesson.py --file path/to/lesson.md
    python3 scripts/ingest_lesson.py --title "Title" --content "Content..."

This script ingests a lesson learned into the RAG system.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.vector_db.chroma_client import get_rag_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_lesson")

def ingest_lesson(file_path=None, title=None, content=None, category="general", severity="medium"):
    db = get_rag_db()
    
    lesson_content = ""
    source = "manual_entry"
    
    if file_path:
        path = Path(file_path)
        if not path.exists():
            # Try relative to project root
            path = PROJECT_ROOT / file_path
            if not path.exists():
                logger.error(f"Lesson file not found: {file_path}")
                return False
        
        with open(path) as f:
            lesson_content = f.read()
        source = path.name
    elif content:
        lesson_content = content
        if title:
            lesson_content = f"# {title}\n\n{content}"
    else:
        logger.error("Must provide --file or --content")
        return False

    logger.info("Ingesting lesson...")

    # Create document
    metadata = {
        "ticker": "LESSON_LEARNED",
        "source": source,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "severity": severity,
    }
    
    doc_id = f"lesson_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Add to DB
    result = db.add_documents(documents=[lesson_content], metadatas=[metadata], ids=[doc_id])

    if result.get("status") == "success":
        logger.info("✅ Lesson learned ingested successfully")
        return True
    else:
        logger.error(f"Failed to ingest: {result.get('message')}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Ingest Lesson Learned")
    parser.add_argument("--file", help="Path to lesson file (markdown/text)")
    parser.add_argument("--title", help="Title of the lesson")
    parser.add_argument("--content", help="Content of the lesson")
    parser.add_argument("--category", default="general", help="Category (backtesting, strategy, etc.)")
    parser.add_argument("--severity", default="medium", help="Severity (low, medium, high, critical)")
    
    args = parser.parse_args()
    
    success = ingest_lesson(
        file_path=args.file,
        title=args.title,
        content=args.content,
        category=args.category,
        severity=args.severity
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
