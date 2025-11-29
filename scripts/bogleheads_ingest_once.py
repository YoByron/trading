#!/usr/bin/env python3
"""
Ingest a single Bogleheads forum snapshot into the Sentiment RAG store.

Prefers the BogleheadsLearner (from .claude skills). Falls back to BogleHeadsAgent
if the learner is unavailable.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict

from src.rag.sentiment_store import SentimentRAGStore, SentimentDocument

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bogleheads_ingest")


def _try_learner() -> Dict:
    try:
        from claude.skills.bogleheads_learner.scripts.bogleheads_learner import (
            BogleheadsLearner,
        )

        learner = BogleheadsLearner()
        return learner.monitor_bogleheads_forum(
            topics=["Personal Investments", "Investing - Theory, News & General"],
            keywords=["rebalancing", "risk", "volatility", "index funds", "ETF"],
            max_posts=30,
            min_replies=3,
        )
    except Exception as e:
        logger.info(f"Learner unavailable or failed: {e}")
        return {}


def _fallback_agent() -> Dict:
    try:
        from src.agents.bogleheads_agent import BogleHeadsAgent

        agent = BogleHeadsAgent()
        result = agent.analyze({"symbol": None})
        return {
            "posts_analyzed": 0,
            "sentiment_summary": result.get("bogleheads_sentiment", "Unknown"),
            "decision": result.get("signal", "HOLD"),
            "confidence": result.get("confidence", 0.5),
            "reasoning": result.get("reasoning", ""),
            "raw": result,
        }
    except Exception as e:
        logger.warning(f"BogleHeadsAgent fallback failed: {e}")
        return {}


def main() -> None:
    # Collect forum snapshot
    snapshot = _try_learner() or _fallback_agent()
    if not snapshot:
        logger.warning("No Bogleheads snapshot collected; exiting")
        return

    # Build RAG document
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    doc_id = f"bogleheads_{now}"
    text = json.dumps(snapshot, ensure_ascii=False)
    metadata = {
        "ticker": "MARKET",
        "published_date": now,
        "sentiment_score": 0.0,
        "confidence": snapshot.get("confidence", "medium"),
        "market_regime": snapshot.get("regime", "unknown"),
        "source_list": "bogleheads_forum",
        "freshness": "live",
        "days_old": 0,
    }

    store = SentimentRAGStore()
    count = store.upsert_documents(
        [SentimentDocument(document_id=doc_id, text=text, metadata=metadata)]
    )
    logger.info("Upserted %d Bogleheads snapshot into RAG", count)


if __name__ == "__main__":
    main()
