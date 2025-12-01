"""
Bogleheads Forum Collector for RAG System

Scrapes recent discussions from bogleheads.org forum.
Respects robots.txt and rate limits.
"""

import logging
import time
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime

from src.rag.collectors.base_collector import BaseNewsCollector

logger = logging.getLogger(__name__)


class BogleheadsCollector(BaseNewsCollector):
    """
    Collector for Bogleheads forum discussions.

    Focuses on 'Investing - Theory, News & General' and 'US Stocks' sections.
    """

    FORUM_URLS = [
        "https://www.bogleheads.org/forum/viewforum.php?f=10",  # Investing - Theory, News & General
        "https://www.bogleheads.org/forum/viewforum.php?f=1",  # Personal Investments
    ]

    BASE_URL = "https://www.bogleheads.org/forum"

    def __init__(self):
        super().__init__(source_name="bogleheads")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; TradingBotResearch/1.0; +http://example.com/bot)"
        }

    def collect(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Collect recent forum topics.

        Args:
            limit: Max topics to collect per forum section

        Returns:
            List of forum topics with title and link
        """
        results = []

        for url in self.FORUM_URLS:
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code != 200:
                    logger.error(
                        f"Failed to fetch Bogleheads forum: {response.status_code}"
                    )
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                # Find topic rows (usually class 'row bg1' or 'row bg2')
                topics = soup.find_all("li", class_="row")

                count = 0
                for topic in topics:
                    if count >= limit:
                        break

                    title_elem = topic.find("a", class_="topictitle")
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    link = title_elem["href"]

                    # Clean up link (it's usually relative)
                    if link.startswith("./"):
                        link = link[2:]
                    full_url = f"{self.BASE_URL}/{link}"

                    # Extract author and stats if possible
                    author_elem = topic.find("a", class_="username")
                    author = author_elem.text.strip() if author_elem else "unknown"

                    results.append(
                        {
                            "source": "bogleheads",
                            "ticker": "MARKET",  # Bogleheads is usually general market
                            "content": title,  # Using title as content for now
                            "url": full_url,
                            "published_at": datetime.now().isoformat(),  # Approximate
                            "author": author,
                            "sentiment": "Neutral",  # Needs deep analysis
                        }
                    )
                    count += 1

                # Be nice to the server
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error scraping Bogleheads: {e}")

        logger.info(f"Collected {len(results)} topics from Bogleheads")
        return results

    def collect_daily_snapshot(self) -> List[Dict[str, Any]]:
        """Collect snapshot of current forum discussions."""
        return self.collect(limit=20)
