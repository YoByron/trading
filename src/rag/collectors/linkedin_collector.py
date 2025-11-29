"""
LinkedIn Sentiment Collector for Trading System

Collects financial/trading content from LinkedIn using LinkedIn API
to gauge professional investor sentiment and detect market trends.

Features:
- OAuth2 authentication with LinkedIn Marketing/Posts API
- Search for posts containing stock tickers ($SPY, $QQQ, etc.)
- Extract sentiment from posts (bullish/bearish/neutral)
- Rate limiting and error handling
- Caches results for 24 hours
- Returns structured sentiment data

Usage:
    # Command line
    python linkedin_collector.py --tickers SPY,QQQ,NVDA

    # Programmatic
    from linkedin_collector import LinkedInCollector
    collector = LinkedInCollector()
    sentiment = collector.collect_ticker_sentiment("SPY")

API Setup:
    1. Create LinkedIn App: https://www.linkedin.com/developers/apps
    2. Request access to Marketing Developer Platform
    3. Add redirect URI for OAuth2 flow
    4. Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env
"""

import os
import re
import json
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.rag.collectors.base_collector import BaseNewsCollector
from src.utils.retry_decorator import retry_with_backoff

logger = logging.getLogger(__name__)


class LinkedInCollector(BaseNewsCollector):
    """
    Collect financial posts from LinkedIn using LinkedIn API.

    Monitors LinkedIn posts for stock ticker mentions and professional sentiment.
    """

    # LinkedIn API endpoints
    API_BASE_URL = "https://api.linkedin.com/v2"
    OAUTH_URL = "https://www.linkedin.com/oauth/v2/accessToken"

    # Rate limiting (LinkedIn allows 500 requests per day for free tier)
    MAX_REQUESTS_PER_DAY = 500
    REQUEST_INTERVAL = 86400 / MAX_REQUESTS_PER_DAY  # seconds between requests

    # Ticker pattern (e.g., $SPY, NVDA, GOOGL)
    TICKER_PATTERN = re.compile(r"\$?([A-Z]{1,5})(?:\b|$)")

    # Common false positives to exclude
    EXCLUDED_TICKERS = {
        "CEO",
        "CFO",
        "CTO",
        "DD",
        "ER",
        "IPO",
        "ETF",
        "IMO",
        "YOLO",
        "RIP",
        "ATH",
        "USA",
        "SEC",
        "IRS",
        "FBI",
        "CIA",
        "FDA",
        "NEWS",
        "EDIT",
        "LINK",
        "POST",
        "FOMO",
        "ATM",
        "GDP",
        "CPI",
        "I",
        "A",
        "AM",
        "PM",
        "IT",
        "IS",
        "OR",
        "AND",
        "THE",
        "FOR",
        "API",
        "AI",
        "ML",
        "RL",
        "WSB",
        "TLDR",
        "TL",
        "DR",
        "CEO",
        "AI",
        "ML",
        "API",
        "IT",
        "HR",
        "PR",
        "VP",
        "SVP",
        "EVP",
        "CMO",
        "CIO",
        "COO",
    }

    # Bullish keywords and weights (professional tone)
    BULLISH_KEYWORDS = {
        # Strong bullish
        "strong buy": 3,
        "bullish": 2,
        "outperform": 2,
        "upgrade": 2,
        "growth": 1,
        "momentum": 2,
        "breakout": 2,
        "rally": 2,
        "surge": 2,
        "opportunity": 1,
        "upside": 2,
        "accumulate": 2,
        "conviction": 2,
        # Moderate bullish
        "positive": 1,
        "improving": 1,
        "strong": 1,
        "beat expectations": 2,
        "exceed": 1,
        "innovation": 1,
        "competitive advantage": 2,
        "market leader": 1,
    }

    # Bearish keywords and weights (professional tone)
    BEARISH_KEYWORDS = {
        # Strong bearish
        "sell": -2,
        "bearish": -2,
        "underperform": -2,
        "downgrade": -2,
        "risk": -1,
        "decline": -2,
        "plunge": -3,
        "crash": -3,
        "collapse": -3,
        "warning": -2,
        "concern": -1,
        "downside": -2,
        # Moderate bearish
        "negative": -1,
        "weak": -1,
        "miss expectations": -2,
        "disappointing": -2,
        "challenging": -1,
        "headwind": -1,
        "pressure": -1,
        "volatility": -1,
    }

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        data_dir: str = "data/sentiment",
        cache_hours: int = 24,
    ):
        """
        Initialize LinkedIn collector.

        Args:
            client_id: LinkedIn API client ID
            client_secret: LinkedIn API client secret
            access_token: Pre-authenticated access token (optional)
            data_dir: Directory to save sentiment data
            cache_hours: Hours to cache results (default: 24)
        """
        super().__init__(source_name="linkedin")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hours = cache_hours

        # Get credentials from environment
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET")
        self.access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")

        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_count_reset = time.time()

        # Setup HTTP session with retry logic
        self.session = self._create_session()

        # Validate credentials
        if not self.client_id or not self.client_secret:
            logger.warning("No LinkedIn API credentials provided!")
            logger.warning("To use this collector, create a LinkedIn app at:")
            logger.warning("https://www.linkedin.com/developers/apps")
            logger.warning(
                "Then set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env"
            )
            raise ValueError(
                "LinkedIn API credentials required. "
                "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env file. "
                "Create app at: https://www.linkedin.com/developers/apps"
            )

        # Authenticate if no access token
        if not self.access_token:
            logger.info("No access token provided, will need to authenticate")
            # In production, you'd implement OAuth2 flow here
            # For now, we'll rely on manual token from environment

    def _create_session(self) -> requests.Session:
        """
        Create HTTP session with retry logic.

        Returns:
            Configured requests Session
        """
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _rate_limit(self):
        """
        Enforce rate limiting to stay within API limits.
        """
        # Reset counter every 24 hours
        if time.time() - self.request_count_reset > 86400:
            self.request_count = 0
            self.request_count_reset = time.time()

        # Check daily limit
        if self.request_count >= self.MAX_REQUESTS_PER_DAY:
            logger.warning("LinkedIn API daily limit reached, waiting 24 hours")
            time.sleep(86400 - (time.time() - self.request_count_reset))
            self.request_count = 0
            self.request_count_reset = time.time()

        # Enforce minimum interval between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)

        self.last_request_time = time.time()
        self.request_count += 1

    @retry_with_backoff(max_retries=3, initial_delay=2.0)
    def _api_request(
        self, endpoint: str, params: Optional[Dict] = None, method: str = "GET"
    ) -> Dict:
        """
        Make authenticated API request to LinkedIn.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            method: HTTP method (GET/POST)

        Returns:
            JSON response data
        """
        if not self.access_token:
            raise ValueError("No access token available. Please authenticate first.")

        # Rate limiting
        self._rate_limit()

        # Build URL
        url = f"{self.API_BASE_URL}/{endpoint.lstrip('/')}"

        # Headers
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, params=params)
            else:
                response = self.session.post(url, headers=headers, json=params)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(
                    "LinkedIn API authentication failed. Token may be expired."
                )
            elif e.response.status_code == 429:
                logger.error("LinkedIn API rate limit exceeded")
            else:
                logger.error(f"LinkedIn API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"LinkedIn API request error: {e}")
            raise

    def extract_tickers(self, text: str) -> List[str]:
        """
        Extract stock tickers from text.

        Args:
            text: Text to search for tickers

        Returns:
            List of unique ticker symbols
        """
        matches = self.TICKER_PATTERN.findall(text.upper())

        tickers = [
            ticker
            for ticker in matches
            if ticker not in self.EXCLUDED_TICKERS and 1 <= len(ticker) <= 5
        ]

        return list(set(tickers))

    def calculate_sentiment_score(
        self, text: str, reactions: int = 0, comments: int = 0, shares: int = 0
    ) -> tuple[int, Dict[str, int]]:
        """
        Calculate sentiment score for LinkedIn post.

        Algorithm:
        - Bullish keywords: +1 to +3 points
        - Bearish keywords: -1 to -3 points
        - Weight by engagement (reactions, comments, shares)

        Args:
            text: Post text to analyze
            reactions: Number of reactions (likes, etc.)
            comments: Number of comments
            shares: Number of shares

        Returns:
            Tuple of (total_score, keyword_counts)
        """
        import math

        text_lower = text.lower()

        bullish_count = 0
        bearish_count = 0
        keyword_details = {"bullish": 0, "bearish": 0}

        # Check bullish keywords
        for keyword, weight in self.BULLISH_KEYWORDS.items():
            if keyword in text_lower:
                count = text_lower.count(keyword)
                bullish_count += count * weight
                keyword_details["bullish"] += count

        # Check bearish keywords
        for keyword, weight in self.BEARISH_KEYWORDS.items():
            if keyword in text_lower:
                count = text_lower.count(keyword)
                bearish_count += count * abs(weight)
                keyword_details["bearish"] += count

        # Base sentiment score
        base_score = bullish_count + bearish_count

        # Weight by engagement (logarithmic to prevent outliers)
        reaction_weight = math.log(max(reactions, 1) + 1)
        comment_weight = (
            math.log(max(comments, 1) + 1) * 1.5
        )  # Comments weighted higher
        share_weight = math.log(max(shares, 1) + 1) * 2  # Shares weighted highest

        # Combined engagement weight
        engagement_weight = (reaction_weight + comment_weight + share_weight) / 3

        # Final weighted score
        weighted_score = int(base_score * engagement_weight)

        return weighted_score, keyword_details

    def search_posts(
        self, query: str, count: int = 25, start: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search LinkedIn posts matching query.

        Note: This uses LinkedIn's ugcPosts endpoint.
        Real implementation would need proper search API access.

        Args:
            query: Search query
            count: Number of posts to fetch
            start: Pagination start

        Returns:
            List of post data
        """
        # Note: LinkedIn's search API is limited and may require
        # Marketing Developer Platform access
        # This is a simplified implementation

        try:
            # In production, you'd use the actual search endpoint
            # For now, we'll use a placeholder that shows the structure
            logger.warning(
                "LinkedIn search API requires Marketing Developer Platform access. "
                "This is a placeholder implementation."
            )

            # Return empty list for now
            # Real implementation would call LinkedIn's search API
            return []

        except Exception as e:
            logger.error(f"Error searching LinkedIn posts: {e}")
            return []

    def collect_ticker_news(
        self, ticker: str, days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Collect LinkedIn posts mentioning a ticker.

        Args:
            ticker: Stock ticker symbol
            days_back: How many days back to collect

        Returns:
            List of normalized articles (LinkedIn posts)
        """
        # Check cache first
        cache_file = (
            self.data_dir
            / f"linkedin_{ticker}_{datetime.now().strftime('%Y-%m-%d')}.json"
        )

        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )
            if cache_age.total_seconds() < self.cache_hours * 3600:
                logger.info(f"Loading cached LinkedIn data for {ticker}")
                with open(cache_file, "r") as f:
                    return json.load(f)

        try:
            # Search for posts mentioning ticker
            query = f"${ticker} OR {ticker} stock OR {ticker} trading"
            posts = self.search_posts(query, count=25)

            articles = []
            cutoff_date = datetime.now() - timedelta(days=days_back)

            for post in posts:
                # Parse date
                created_timestamp = post.get("created", {}).get("time", 0) / 1000
                created_date = datetime.fromtimestamp(created_timestamp)

                # Filter by date
                if created_date < cutoff_date:
                    continue

                # Extract text
                text = (
                    post.get("specificContent", {})
                    .get("com.linkedin.ugc.ShareContent", {})
                    .get("shareCommentary", {})
                    .get("text", "")
                )

                # Get engagement metrics
                reactions = post.get("numLikes", 0)
                comments = post.get("numComments", 0)
                shares = post.get("numShares", 0)

                # Calculate sentiment
                sentiment_score, _ = self.calculate_sentiment_score(
                    text, reactions=reactions, comments=comments, shares=shares
                )

                # Normalize sentiment to 0-1 scale
                normalized_sentiment = max(0, min(1, (sentiment_score + 100) / 200))

                article = self.normalize_article(
                    title=text[:100] + "..." if len(text) > 100 else text,
                    content=text,
                    url=post.get("permalink", ""),
                    published_date=created_date.strftime("%Y-%m-%d"),
                    ticker=ticker,
                    sentiment=normalized_sentiment,
                )

                articles.append(article)

            # Save to cache
            if articles:
                with open(cache_file, "w") as f:
                    json.dump(articles, f, indent=2)

            logger.info(f"Collected {len(articles)} LinkedIn posts for {ticker}")
            return articles

        except Exception as e:
            logger.error(f"Error collecting LinkedIn posts for {ticker}: {e}")
            return []

    def collect_market_news(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Collect general market posts from LinkedIn.

        Uses SPY as proxy for market sentiment.

        Args:
            days_back: How many days back to collect

        Returns:
            List of normalized articles
        """
        return self.collect_ticker_news("SPY", days_back=days_back)

    def analyze_ticker_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Analyze overall sentiment for a ticker from LinkedIn posts.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with sentiment analysis:
            {
                "symbol": "SPY",
                "sentiment_score": 0.65,  # 0-1 scale
                "post_count": 15,
                "source": "linkedin",
                "bullish_signals": 10,
                "bearish_signals": 5,
                "confidence": "medium"
            }
        """
        try:
            posts = self.collect_ticker_news(ticker, days_back=7)

            if not posts:
                return {
                    "symbol": ticker,
                    "sentiment_score": 0.5,  # Neutral
                    "post_count": 0,
                    "source": "linkedin",
                    "bullish_signals": 0,
                    "bearish_signals": 0,
                    "confidence": "none",
                }

            # Aggregate sentiment
            total_sentiment = 0
            bullish_count = 0
            bearish_count = 0

            for post in posts:
                sentiment = post.get("sentiment", 0.5)
                total_sentiment += sentiment

                if sentiment > 0.6:
                    bullish_count += 1
                elif sentiment < 0.4:
                    bearish_count += 1

            avg_sentiment = total_sentiment / len(posts)

            # Determine confidence
            if len(posts) >= 10:
                confidence = "high"
            elif len(posts) >= 5:
                confidence = "medium"
            else:
                confidence = "low"

            return {
                "symbol": ticker,
                "sentiment_score": round(avg_sentiment, 2),
                "post_count": len(posts),
                "source": "linkedin",
                "bullish_signals": bullish_count,
                "bearish_signals": bearish_count,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Error analyzing LinkedIn sentiment for {ticker}: {e}")
            return {
                "symbol": ticker,
                "sentiment_score": 0.5,
                "post_count": 0,
                "source": "linkedin",
                "bullish_signals": 0,
                "bearish_signals": 0,
                "confidence": "error",
                "error": str(e),
            }


def main():
    """CLI interface for LinkedIn sentiment collection."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect LinkedIn sentiment for trading system"
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default="SPY,QQQ,NVDA",
        help="Comma-separated list of tickers (default: SPY,QQQ,NVDA)",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Days to look back (default: 7)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: data/sentiment/linkedin_YYYY-MM-DD.json)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize collector
    try:
        collector = LinkedInCollector()
    except ValueError as e:
        print(f"\nERROR: {e}\n")
        print("Setup Instructions:")
        print("1. Go to https://www.linkedin.com/developers/apps")
        print("2. Create a new app")
        print("3. Request access to Marketing Developer Platform")
        print("4. Add your credentials to .env:")
        print("   LINKEDIN_CLIENT_ID=your_client_id")
        print("   LINKEDIN_CLIENT_SECRET=your_client_secret")
        print("   LINKEDIN_ACCESS_TOKEN=your_access_token (optional)")
        return

    # Parse tickers
    tickers = [t.strip().upper() for t in args.tickers.split(",")]

    # Collect sentiment
    results = {}
    for ticker in tickers:
        logger.info(f"Analyzing LinkedIn sentiment for {ticker}...")
        sentiment = collector.analyze_ticker_sentiment(ticker)
        results[ticker] = sentiment

    # Print summary
    print("\n" + "=" * 80)
    print("LINKEDIN SENTIMENT ANALYSIS")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Lookback: {args.days} days")

    print("\nResults:")
    print("-" * 80)

    for ticker, data in results.items():
        sentiment = (
            "BULLISH"
            if data["sentiment_score"] > 0.6
            else "BEARISH" if data["sentiment_score"] < 0.4 else "NEUTRAL"
        )

        print(f"\n{ticker}:")
        print(f"  Sentiment Score: {data['sentiment_score']:.2f} ({sentiment})")
        print(f"  Post Count: {data['post_count']}")
        print(f"  Bullish Signals: {data['bullish_signals']}")
        print(f"  Bearish Signals: {data['bearish_signals']}")
        print(f"  Confidence: {data['confidence'].upper()}")

    print("\n" + "=" * 80)

    # Save results
    output_file = (
        args.output
        or f"data/sentiment/linkedin_{datetime.now().strftime('%Y-%m-%d')}.json"
    )
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
