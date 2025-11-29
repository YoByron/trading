"""
News Collection Orchestrator

Coordinates all news collectors and aggregates results.
"""

from typing import List, Dict, Any
from datetime import datetime
import logging
import json
import os

from src.rag.collectors.yahoo_collector import YahooFinanceCollector
from src.rag.collectors.reddit_collector import RedditCollector
from src.rag.collectors.alphavantage_collector import AlphaVantageCollector
from src.rag.collectors.tiktok_collector import TikTokCollector

logger = logging.getLogger(__name__)


class NewsOrchestrator:
    """
    Orchestrate multiple news collectors.

    Coordinates:
    - Yahoo Finance (yfinance API)
    - Reddit (praw API)
    - Alpha Vantage (sentiment API)
    - TikTok (Research API)

    Future additions:
    - Bloomberg (web scraping)
    - Seeking Alpha (web scraping)
    - Google Finance (web scraping)
    """

    def __init__(self):
        """Initialize all collectors."""
        self.collectors = {
            "yahoo": YahooFinanceCollector(),
            "reddit": RedditCollector(),
            "alphavantage": AlphaVantageCollector(),
            "tiktok": TikTokCollector(),
        }

        logger.info(f"Initialized {len(self.collectors)} news collectors")

    def collect_all_ticker_news(
        self, ticker: str, days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Collect news for a ticker from ALL sources.

        Args:
            ticker: Stock ticker symbol
            days_back: How many days back to collect

        Returns:
            Aggregated list of articles from all sources
        """
        all_articles = []

        for source_name, collector in self.collectors.items():
            try:
                logger.info(f"Collecting {ticker} news from {source_name}...")
                articles = collector.collect_ticker_news(ticker, days_back=days_back)
                all_articles.extend(articles)

                logger.info(f"  ✅ {source_name}: {len(articles)} articles")

            except Exception as e:
                logger.error(f"  ❌ {source_name} failed: {e}")

        # Deduplicate by URL
        all_articles = self._deduplicate(all_articles)

        logger.info(f"Collected {len(all_articles)} total articles for {ticker}")
        return all_articles

    def collect_watchlist_news(
        self, tickers: List[str], days_back: int = 7
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect news for multiple tickers (watchlist).

        Args:
            tickers: List of ticker symbols
            days_back: How many days back to collect

        Returns:
            Dict mapping ticker -> list of articles
        """
        results = {}

        for ticker in tickers:
            logger.info(f"\n📰 Collecting news for {ticker}...")
            articles = self.collect_all_ticker_news(ticker, days_back=days_back)
            results[ticker] = articles

        total_articles = sum(len(articles) for articles in results.values())
        logger.info(
            f"\n✅ Collected {total_articles} total articles for {len(tickers)} tickers"
        )

        return results

    def collect_market_news(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Collect general market news from ALL sources.

        Args:
            days_back: How many days back to collect

        Returns:
            Aggregated market news
        """
        all_articles = []

        for source_name, collector in self.collectors.items():
            try:
                logger.info(f"Collecting market news from {source_name}...")
                articles = collector.collect_market_news(days_back=days_back)
                all_articles.extend(articles)

                logger.info(f"  ✅ {source_name}: {len(articles)} articles")

            except Exception as e:
                logger.error(f"  ❌ {source_name} failed: {e}")

        # Deduplicate
        all_articles = self._deduplicate(all_articles)

        logger.info(f"Collected {len(all_articles)} total market articles")
        return all_articles

    def save_collected_news(self, articles: List[Dict[str, Any]], ticker: str = None):
        """
        Save collected news to data/rag/normalized/.

        Args:
            articles: List of normalized articles
            ticker: Optional ticker (for filename)
        """
        if not articles:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticker_suffix = f"_{ticker}" if ticker else "_market"
        filename = f"data/rag/normalized/news{ticker_suffix}_{timestamp}.json"

        os.makedirs("data/rag/normalized", exist_ok=True)

        try:
            with open(filename, "w") as f:
                json.dump(articles, f, indent=2)

            logger.info(f"💾 Saved {len(articles)} articles to {filename}")

        except Exception as e:
            logger.error(f"Error saving articles: {e}")

    def _deduplicate(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate articles based on URL.

        Args:
            articles: List of articles

        Returns:
            Deduplicated list
        """
        seen_urls = set()
        unique_articles = []

        for article in articles:
            url = article.get("url", "")

            # Skip if no URL or already seen
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            unique_articles.append(article)

        duplicates_removed = len(articles) - len(unique_articles)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate articles")

        return unique_articles


# Singleton instance
_orchestrator_instance = None


def get_orchestrator() -> NewsOrchestrator:
    """
    Get or create NewsOrchestrator instance (singleton).

    Returns:
        NewsOrchestrator instance
    """
    global _orchestrator_instance

    if _orchestrator_instance is None:
        _orchestrator_instance = NewsOrchestrator()

    return _orchestrator_instance
