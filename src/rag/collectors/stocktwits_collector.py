"""
StockTwits Collector for RAG System

Collects sentiment and messages from StockTwits API.
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.rag.collectors.base_collector import BaseNewsCollector

logger = logging.getLogger(__name__)


class StockTwitsCollector(BaseNewsCollector):
    """
    Collector for StockTwits data.

    Uses the public API to fetch messages for specific symbols.
    """

    BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"

    def __init__(self):
        super().__init__(source_name="stocktwits")

    def collect(self, ticker: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Collect messages for a specific ticker.

        Args:
            ticker: Stock symbol (e.g., "AAPL")
            limit: Number of messages to retrieve (default 30)

        Returns:
            List of dictionaries containing message data
        """
        url = self.BASE_URL.format(symbol=ticker)

        try:
            response = requests.get(url)

            if response.status_code == 429:
                logger.warning(f"Rate limit exceeded for StockTwits ({ticker})")
                return []

            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch StockTwits data for {ticker}: {response.status_code}"
                )
                return []

            data = response.json()
            messages = data.get("messages", [])

            results = []
            for msg in messages[:limit]:
                # Extract sentiment if available
                sentiment = "Neutral"
                if msg.get("entities") and msg["entities"].get("sentiment"):
                    sentiment = msg["entities"]["sentiment"]["basic"]

                entry = {
                    "source": "stocktwits",
                    "ticker": ticker,
                    "content": msg.get("body", ""),
                    "url": f"https://stocktwits.com/message/{msg.get('id')}",
                    "published_at": msg.get("created_at"),
                    "sentiment": sentiment,
                    "author": msg.get("user", {}).get("username", "unknown"),
                    "raw_score": 0.0,  # Placeholder, would need NLP to score properly
                }
                results.append(entry)

            logger.info(
                f"Collected {len(results)} messages from StockTwits for {ticker}"
            )
            return results

        except Exception as e:
            logger.error(f"Error collecting from StockTwits for {ticker}: {e}")
            return []

    def collect_daily_snapshot(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """Collect latest messages for all tracked tickers."""
        all_messages = []
        for ticker in tickers:
            messages = self.collect(ticker)
            all_messages.extend(messages)
        return all_messages
