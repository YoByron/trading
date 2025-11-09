# Sentiment Analysis RAG System Architecture

**Project**: AI Trading System - Sentiment Intelligence Layer
**Author**: CTO (Claude Agent)
**Date**: November 9, 2025
**Status**: Phase 1 Implemented (SQLite metadata + Chroma vector store live)
**Location**: `/Users/igorganapolsky/workspace/git/apps/trading`

---

## Executive Summary

This document defines a comprehensive Retrieval-Augmented Generation (RAG) system for aggregating multi-source sentiment data to enhance trading decisions. The system operates BEFORE market open (9:35 AM ET execution), aggregating sentiment from 7+ free sources and storing it in a queryable format for CoreStrategy (Tier 1) and GrowthStrategy (Tier 2).

**Key Constraints**:
- 100% FREE tier APIs (no paid services)
- Executes daily at 8:00 AM ET (1.5 hours before market open)
- All sources respect rate limits
- Sentiment feeds into existing MACD + RSI + Volume system
- Storage: JSON snapshots + SQLite metadata + Chroma vector store

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SENTIMENT RAG PIPELINE                        │
│                  (Runs Daily 8:00 AM ET)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────┐
    │         PHASE 1: DATA COLLECTION (8:00-8:45 AM)  │
    └──────────────────────────────────────────────────┘
              │
              ├─► [Alpha Vantage] News + Sentiment (25 calls/day FREE)
              │       │
              │       └─► Per-ticker sentiment scores + news headlines
              │
              ├─► [Reddit API] Social Sentiment (100 req/min FREE)
              │       │
              │       └─► r/wallstreetbets + r/stocks + r/investing
              │
              ├─► [Yahoo Finance RSS] News Feed (Unlimited FREE)
              │       │
              │       └─► Latest headlines + descriptions
              │
              ├─► [Finnhub] Market News (60 calls/min FREE)
              │       │
              │       └─► Company news + press releases
              │
              ├─► [FRED API] Macro Economics (Unlimited FREE)
              │       │
              │       └─► Interest rates + employment + GDP data
              │
              ├─► [SEC EDGAR] Filings (Rate limited FREE)
              │       │
              │       └─► 8-K events + insider transactions
              │
              └─► [YouTube] Video Analysis (Existing)
                      │
                      └─► Stock picks from financial influencers
                              │
                              ▼
    ┌──────────────────────────────────────────────────┐
    │     PHASE 2: SENTIMENT SCORING (8:45-9:00 AM)    │
    └──────────────────────────────────────────────────┘
              │
              ├─► Per-Ticker Aggregation
              │       │
              │       └─► Combine all sources for SPY, QQQ, VOO, NVDA, GOOGL, AMZN
              │
              ├─► Normalization (0-100 scale)
              │       │
              │       └─► Reddit upvotes, news tone, analyst ratings → unified score
              │
              ├─► Confidence Weighting
              │       │
              │       └─► Alpha Vantage: 30%, Reddit: 20%, News: 20%, YouTube: 15%, SEC: 10%, FRED: 5%
              │
              └─► Market Regime Detection
                      │
                      └─► Bullish / Neutral / Bearish / Risk-Off
                              │
                              ▼
    ┌──────────────────────────────────────────────────┐
    │         PHASE 3: STORAGE (9:00-9:15 AM)          │
    └──────────────────────────────────────────────────┘
              │
              ├─► JSON Database (Primary)
              │       │
              │       └─► data/sentiment/YYYY-MM-DD.json
              │               │
              │               ├─► Ticker-level scores
              │               ├─► Market regime
              │               └─► Source breakdowns
              │
              ├─► Historical Tracking (30-90 days)
              │       │
              │       └─► data/sentiment/history.json
              │
              └─► SQLite (Optional - Phase 2 upgrade)
                      │
                      └─► Faster queries, better analytics
                              │
                              ▼
    ┌──────────────────────────────────────────────────┐
    │    PHASE 4: INTEGRATION (9:15-9:35 AM)           │
    └──────────────────────────────────────────────────┘
              │
              ├─► CoreStrategy (Tier 1: SPY/QQQ/VOO)
              │       │
              │       └─► Sentiment = go/no-go filter
              │           Example: If market_regime == "risk_off" → SKIP TRADE
              │
              └─► GrowthStrategy (Tier 2: NVDA/GOOGL/AMZN)
                      │
                      └─► Sentiment = scoring modifier
                          Example: High sentiment → +10 points to technical score
                              │
                              ▼
                    ┌──────────────────────┐
                    │  9:35 AM: EXECUTE    │
                    │  (Sentiment-Aware)   │
                    └──────────────────────┘
```

---

## 2. Data Sources & Integration

### 2.1 Alpha Vantage (News & Sentiment API)

**Endpoint**: `https://www.alpha vantage.co/query?function=NEWS_SENTIMENT`
**Free Tier**: 25 API calls/day
**Strategy**: Use for Tier 1 + Tier 2 tickers (6 tickers = 6 calls)

**Data Returned**:
```json
{
  "ticker": "SPY",
  "sentiment_score": 0.25,  // -1 (bearish) to +1 (bullish)
  "sentiment_label": "Somewhat-Bullish",
  "relevance_score": 0.85,  // How relevant to ticker
  "news_count": 12,
  "top_headlines": [
    "S&P 500 rallies on strong earnings",
    "Fed signals pause in rate hikes"
  ]
}
```

**Implementation**:
```python
# src/utils/alpha_vantage_client.py
import requests
import os

class AlphaVantageClient:
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"

    def get_news_sentiment(self, ticker: str):
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": self.api_key,
            "limit": 50  # Get 50 most recent articles
        }
        response = requests.get(self.base_url, params=params)
        return response.json()
```

**Timeline**: 1-2 hours to implement

---

### 2.2 Reddit API (Social Sentiment)

**Endpoint**: Reddit API via PRAW library
**Free Tier**: 100 requests/minute
**Strategy**: Monitor r/wallstreetbets, r/stocks, r/investing for mentions

**Data Returned**:
```json
{
  "ticker": "NVDA",
  "mentions": 47,
  "avg_upvotes": 234,
  "sentiment_breakdown": {
    "bullish": 32,  // Posts with positive sentiment
    "bearish": 8,
    "neutral": 7
  },
  "top_post": {
    "title": "NVDA earnings beat - $150 PT",
    "upvotes": 1842,
    "comments": 312
  }
}
```

**Implementation**:
```python
# src/utils/reddit_client.py
import praw
import os
from datetime import datetime, timedelta

class RedditSentimentAnalyzer:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="trading-sentiment-bot v1.0"
        )
        self.subreddits = ["wallstreetbets", "stocks", "investing"]

    def analyze_ticker(self, ticker: str, lookback_hours: int = 24):
        mentions = []
        for subreddit_name in self.subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            # Search posts mentioning ticker
            for post in subreddit.search(ticker, time_filter="day", limit=100):
                if self._is_recent(post.created_utc, lookback_hours):
                    mentions.append({
                        "title": post.title,
                        "upvotes": post.score,
                        "comments": post.num_comments,
                        "sentiment": self._analyze_sentiment(post.title)
                    })
        return self._aggregate_mentions(mentions)
```

**Timeline**: 2-3 hours to implement

---

### 2.3 Yahoo Finance RSS (News Feed)

**Endpoint**: `https://finance.yahoo.com/rss/`
**Free Tier**: Unlimited
**Strategy**: Parse RSS feeds for ticker-specific news

**Data Returned**:
```json
{
  "ticker": "GOOGL",
  "headlines": [
    {
      "title": "Alphabet reports Q3 earnings beat",
      "published": "2025-11-08T16:05:00",
      "summary": "Google parent Alphabet Inc reported...",
      "source": "Reuters"
    }
  ],
  "news_count": 8
}
```

**Implementation**:
```python
# src/utils/yahoo_rss_parser.py
import feedparser

class YahooNewsParser:
    def get_ticker_news(self, ticker: str):
        url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        feed = feedparser.parse(url)
        return [
            {
                "title": entry.title,
                "published": entry.published,
                "summary": entry.summary,
                "link": entry.link
            }
            for entry in feed.entries
        ]
```

**Timeline**: 1 hour to implement

---

### 2.4 Finnhub (Market News)

**Endpoint**: `https://finnhub.io/api/v1/company-news`
**Free Tier**: 60 API calls/minute
**Strategy**: Get company-specific news and press releases

**Data Returned**:
```json
{
  "ticker": "AMZN",
  "news": [
    {
      "headline": "Amazon Web Services signs $38B OpenAI deal",
      "datetime": 1699459200,
      "source": "Bloomberg",
      "summary": "AWS secures major AI infrastructure contract...",
      "sentiment": "positive"
    }
  ]
}
```

**Implementation**:
```python
# src/utils/finnhub_client.py
import requests
import os

class FinnhubClient:
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        self.base_url = "https://finnhub.io/api/v1"

    def get_company_news(self, ticker: str, days_back: int = 7):
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.base_url}/company-news"
        params = {
            "symbol": ticker,
            "from": from_date,
            "to": to_date,
            "token": self.api_key
        }
        return requests.get(url, params=params).json()
```

**Timeline**: 1 hour to implement

---

### 2.5 FRED API (Macro Economics)

**Endpoint**: `https://api.stlouisfed.org/fred/series/observations`
**Free Tier**: Unlimited
**Strategy**: Track macro indicators (interest rates, unemployment, GDP)

**Data Returned**:
```json
{
  "indicators": {
    "fed_funds_rate": 5.50,
    "unemployment_rate": 3.8,
    "10y_treasury_yield": 4.45,
    "vix_index": 18.2
  },
  "market_regime": "neutral"  // Based on indicator thresholds
}
```

**Implementation**:
```python
# src/utils/fred_client.py
import requests
import os

class FREDClient:
    INDICATORS = {
        "fed_funds_rate": "DFF",
        "unemployment": "UNRATE",
        "treasury_10y": "DGS10",
        "gdp_growth": "A191RL1Q225SBEA"
    }

    def __init__(self):
        self.api_key = os.getenv("FRED_API_KEY")
        self.base_url = "https://api.stlouisfed.org/fred"

    def get_latest_indicators(self):
        data = {}
        for name, series_id in self.INDICATORS.items():
            url = f"{self.base_url}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": 1,
                "sort_order": "desc"
            }
            response = requests.get(url, params=params).json()
            data[name] = float(response["observations"][0]["value"])
        return data
```

**Timeline**: 1 hour to implement

---

### 2.6 SEC EDGAR (Filings)

**Endpoint**: `https://www.sec.gov/cgi-bin/browse-edgar`
**Free Tier**: Rate limited (10 requests/second)
**Strategy**: Monitor 8-K filings (material events) and insider transactions

**Data Returned**:
```json
{
  "ticker": "NVDA",
  "recent_filings": [
    {
      "form_type": "8-K",
      "filed_date": "2025-11-07",
      "description": "Results of Operations and Financial Condition",
      "url": "https://www.sec.gov/..."
    }
  ],
  "insider_activity": {
    "buys": 3,
    "sells": 1,
    "net_sentiment": "bullish"
  }
}
```

**Implementation**:
```python
# src/utils/sec_edgar_client.py
import requests
from bs4 import BeautifulSoup

class SECEdgarClient:
    def __init__(self):
        self.base_url = "https://www.sec.gov"
        self.headers = {
            "User-Agent": "TradingSystem/1.0 (contact@example.com)"
        }

    def get_recent_filings(self, ticker: str, forms: list = ["8-K"]):
        # Search for recent filings
        search_url = f"{self.base_url}/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "CIK": ticker,
            "type": ",".join(forms),
            "count": 10
        }
        response = requests.get(search_url, params=params, headers=self.headers)
        # Parse HTML response
        # ... (implementation details)
```

**Timeline**: 2-3 hours to implement

---

### 2.7 YouTube Analysis (Existing)

**Status**: Already implemented (`scripts/youtube_monitor.py`)
**Data**: Stock picks from financial influencers
**Integration**: Pull from existing watchlist updates

**Data Returned**:
```json
{
  "ticker": "AMZN",
  "source": "Parkev Tatevosian CFA",
  "sentiment": "bullish",
  "confidence": "high",
  "rationale": "$38B OpenAI deal, 15% upside to fair value",
  "date": "2025-11-05"
}
```

**Timeline**: 30 minutes to integrate

---

## 3. Sentiment Scoring & Normalization

### 3.1 Per-Source Scoring (0-100 scale)

Each source provides a raw score that we normalize to 0-100:

| Source | Raw Data | Normalization Formula | Weight |
|--------|----------|----------------------|--------|
| **Alpha Vantage** | -1 to +1 sentiment | `(score + 1) * 50` | 30% |
| **Reddit** | Upvotes + mentions | `min(100, (upvotes/50 + mentions*2))` | 20% |
| **Yahoo RSS** | News count | `min(100, news_count * 10)` | 10% |
| **Finnhub** | News sentiment | Keyword analysis → 0-100 | 15% |
| **YouTube** | Analyst rating | High=90, Medium=60, Low=30 | 15% |
| **SEC** | Insider buys | Buys=+20, Sells=-20 | 5% |
| **FRED** | VIX + rates | Risk-off indicator | 5% |

### 3.2 Aggregate Sentiment Score

```python
def calculate_aggregate_sentiment(ticker: str, source_data: dict) -> dict:
    """
    Aggregate sentiment from all sources into single score.

    Returns:
        {
            "ticker": "SPY",
            "aggregate_score": 67.5,  // 0-100 (0=bearish, 50=neutral, 100=bullish)
            "confidence": 0.82,       // 0-1 based on source agreement
            "sources": {
                "alpha_vantage": 72,
                "reddit": 65,
                "yahoo": 60,
                "finnhub": 70,
                "youtube": 75,
                "sec": 55,
                "fred": 50
            },
            "recommendation": "BULLISH"  // VERY_BULLISH, BULLISH, NEUTRAL, BEARISH, VERY_BEARISH
        }
    """
    weights = {
        "alpha_vantage": 0.30,
        "reddit": 0.20,
        "finnhub": 0.15,
        "youtube": 0.15,
        "yahoo": 0.10,
        "sec": 0.05,
        "fred": 0.05
    }

    weighted_score = sum(
        source_data[source] * weight
        for source, weight in weights.items()
        if source in source_data
    )

    # Confidence = agreement between sources (low std dev = high confidence)
    scores = [source_data[s] for s in source_data if s in weights]
    std_dev = np.std(scores)
    confidence = max(0, 1 - (std_dev / 50))  // Lower variance = higher confidence

    # Classify sentiment
    if weighted_score >= 70:
        recommendation = "VERY_BULLISH"
    elif weighted_score >= 55:
        recommendation = "BULLISH"
    elif weighted_score >= 45:
        recommendation = "NEUTRAL"
    elif weighted_score >= 30:
        recommendation = "BEARISH"
    else:
        recommendation = "VERY_BEARISH"

    return {
        "ticker": ticker,
        "aggregate_score": weighted_score,
        "confidence": confidence,
        "sources": source_data,
        "recommendation": recommendation,
        "timestamp": datetime.now().isoformat()
    }
```

### 3.3 Market Regime Detection

Use FRED data to detect overall market conditions:

```python
def detect_market_regime(fred_data: dict) -> str:
    """
    Determine market regime based on macro indicators.

    Returns: "bullish", "neutral", "bearish", "risk_off"
    """
    fed_rate = fred_data["fed_funds_rate"]
    unemployment = fred_data["unemployment"]
    vix = fred_data.get("vix_index", 15)  # Default if unavailable

    # Risk-off: VIX > 30
    if vix > 30:
        return "risk_off"

    # Bearish: Rising rates + rising unemployment
    if fed_rate > 5.0 and unemployment > 4.5:
        return "bearish"

    # Bullish: Low rates + low unemployment + low VIX
    if fed_rate < 3.0 and unemployment < 4.0 and vix < 15:
        return "bullish"

    # Default: Neutral
    return "neutral"
```

---

## 4. Storage Schema

### 4.1 Daily Sentiment File

**Location**: `data/sentiment/YYYY-MM-DD.json`

```json
{
  "meta": {
    "date": "2025-11-09",
    "generated_at": "2025-11-09T08:45:00",
    "market_regime": "neutral",
    "vix": 18.2,
    "fed_funds_rate": 5.50
  },
  "tickers": {
    "SPY": {
      "aggregate_score": 67.5,
      "confidence": 0.82,
      "recommendation": "BULLISH",
      "sources": {
        "alpha_vantage": {
          "score": 72,
          "sentiment_label": "Bullish",
          "news_count": 12,
          "top_headline": "S&P 500 rallies on strong earnings"
        },
        "reddit": {
          "score": 65,
          "mentions": 23,
          "avg_upvotes": 145,
          "sentiment": "bullish"
        },
        "yahoo": {
          "score": 60,
          "news_count": 6
        },
        "finnhub": {
          "score": 70,
          "news_count": 8
        },
        "youtube": {
          "score": 75,
          "analyst": "N/A",
          "recommendation": "N/A"
        },
        "sec": {
          "score": 55,
          "insider_buys": 2,
          "insider_sells": 1
        },
        "fred": {
          "score": 50,
          "regime": "neutral"
        }
      }
    },
    "NVDA": {
      "aggregate_score": 82.3,
      "confidence": 0.91,
      "recommendation": "VERY_BULLISH",
      "sources": {
        // ... similar structure
      }
    }
    // ... QQQ, VOO, GOOGL, AMZN
  }
}
```

### 4.2 Historical Tracking

**Location**: `data/sentiment/history.json`

```json
{
  "SPY": [
    {
      "date": "2025-11-09",
      "score": 67.5,
      "recommendation": "BULLISH"
    },
    {
      "date": "2025-11-08",
      "score": 72.1,
      "recommendation": "BULLISH"
    }
    // ... last 90 days
  ],
  "NVDA": [
    // ... last 90 days
  ]
}
```

### 4.3 SQLite Schema (Optional Upgrade - Phase 2)

```sql
-- Table: sentiment_daily
CREATE TABLE sentiment_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    aggregate_score REAL NOT NULL,
    confidence REAL NOT NULL,
    recommendation VARCHAR(20) NOT NULL,
    av_score REAL,
    reddit_score REAL,
    yahoo_score REAL,
    finnhub_score REAL,
    youtube_score REAL,
    sec_score REAL,
    fred_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, ticker)
);

-- Table: market_regime
CREATE TABLE market_regime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    regime VARCHAR(20) NOT NULL,
    vix REAL,
    fed_funds_rate REAL,
    unemployment REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookups
CREATE INDEX idx_sentiment_ticker_date ON sentiment_daily(ticker, date DESC);
```

---

## 5. Integration with Trading Strategies

### 5.1 CoreStrategy (Tier 1: SPY/QQQ/VOO)

**Role**: Sentiment as go/no-go filter

```python
# src/strategies/core_strategy.py (MODIFIED)

def execute_daily(self) -> Optional[TradeOrder]:
    """Execute daily with sentiment filtering."""

    # Step 1: Load sentiment data
    sentiment_data = self._load_daily_sentiment()

    # Step 2: Check market regime
    market_regime = sentiment_data["meta"]["market_regime"]

    if market_regime == "risk_off":
        logger.warning("🚨 RISK-OFF REGIME - Pausing new purchases")
        return None

    # Step 3: Calculate momentum scores (existing logic)
    momentum_scores = self._calculate_all_momentum_scores(sentiment)

    # Step 4: Select best ETF
    best_etf = self.select_best_etf(momentum_scores)

    # Step 5: Check ETF-specific sentiment
    etf_sentiment = sentiment_data["tickers"][best_etf]

    if etf_sentiment["recommendation"] in ["BEARISH", "VERY_BEARISH"]:
        logger.warning(f"⚠️ {best_etf} sentiment is {etf_sentiment['recommendation']} - SKIPPING")
        return None

    # Step 6: Proceed with order (existing logic)
    # ...
```

**Impact**:
- Prevents buying during market crashes (VIX > 30)
- Skips trades on bearish sentiment days
- Reduces losses during negative news cycles

---

### 5.2 GrowthStrategy (Tier 2: NVDA/GOOGL/AMZN)

**Role**: Sentiment as scoring modifier

```python
# src/strategies/growth_strategy.py (MODIFIED)

def calculate_technical_score(self, symbol: str) -> float:
    """Calculate technical score with sentiment boost."""

    # Step 1: Calculate base technical score (existing)
    base_score = self._calculate_base_technical_score(symbol)

    # Step 2: Load sentiment
    sentiment_data = self._load_daily_sentiment()
    ticker_sentiment = sentiment_data["tickers"].get(symbol, {})

    # Step 3: Apply sentiment modifier
    sentiment_boost = self._calculate_sentiment_boost(ticker_sentiment)

    # Step 4: Combine scores
    final_score = base_score + sentiment_boost

    logger.info(
        f"{symbol}: base_score={base_score:.1f}, sentiment_boost={sentiment_boost:.1f}, "
        f"final={final_score:.1f}"
    )

    return min(100, max(0, final_score))

def _calculate_sentiment_boost(self, sentiment: dict) -> float:
    """
    Convert sentiment to score modifier.

    Returns: -20 to +20 points
    """
    if not sentiment:
        return 0.0

    aggregate_score = sentiment.get("aggregate_score", 50)
    confidence = sentiment.get("confidence", 0.5)

    # Map 0-100 sentiment to -20 to +20 boost
    # Example: 80 score, 0.9 confidence → +18 boost
    normalized = (aggregate_score - 50) / 50  # -1 to +1
    boost = normalized * 20 * confidence

    return boost
```

**Impact**:
- High sentiment → +15 to +20 points (increases buy probability)
- Low sentiment → -15 to -20 points (decreases buy probability)
- YouTube picks get extra weight via confidence score

---

## 6. Execution Schedule & Performance

### 6.1 Daily Execution Timeline

```
07:55 AM ET - System wakes up
08:00 AM ET - PHASE 1: Data Collection Starts
  └─ Parallel API calls (Alpha Vantage, Reddit, Yahoo, Finnhub, FRED, SEC)
  └─ Duration: ~15-20 minutes (parallelized)

08:20 AM ET - PHASE 2: Sentiment Scoring
  └─ Normalize scores for each ticker
  └─ Calculate aggregate scores
  └─ Detect market regime
  └─ Duration: ~5-10 minutes

08:30 AM ET - PHASE 3: Storage
  └─ Write data/sentiment/YYYY-MM-DD.json
  └─ Update data/sentiment/history.json
  └─ Duration: ~1-2 minutes

08:35 AM ET - PHASE 4: Integration
  └─ CoreStrategy + GrowthStrategy load sentiment data
  └─ Ready for 9:35 AM execution

09:35 AM ET - EXECUTE TRADES (Sentiment-Aware)
```

### 6.2 Cron Configuration

```bash
# crontab -e
# Monday-Friday at 8:00 AM ET
0 8 * * 1-5 cd /Users/igorganapolsky/workspace/git/apps/trading && /Users/igorganapolsky/workspace/git/apps/trading/venv/bin/python scripts/sentiment_aggregator.py >> logs/sentiment.log 2>&1
```

### 6.3 Rate Limit Management

| Source | Limit | Daily Usage | Strategy |
|--------|-------|-------------|----------|
| Alpha Vantage | 25/day | 6 calls (Tier 1+2 tickers) | Cache results for 24 hours |
| Reddit | 100/min | ~30 calls | Batch requests per subreddit |
| Yahoo RSS | Unlimited | 6 calls | No limits |
| Finnhub | 60/min | 6 calls | No limits |
| FRED | Unlimited | 4 calls (macro indicators) | No limits |
| SEC | 10/sec | 6 calls | Rate limit to 1/sec |
| YouTube | Unlimited | Already cached | Use existing data |

**Total Daily Calls**: ~60 calls across all sources
**Total Execution Time**: 25-35 minutes
**Cost**: $0 (100% free tier)

---

## 7. Error Handling & Fallbacks

### 7.1 API Failures

```python
def get_sentiment_with_fallback(ticker: str) -> dict:
    """
    Attempt to get sentiment with graceful degradation.
    """
    sentiment_data = {
        "ticker": ticker,
        "aggregate_score": 50,  # Neutral default
        "confidence": 0.0,
        "recommendation": "NEUTRAL",
        "sources": {}
    }

    # Try each source with individual error handling
    try:
        av_data = alpha_vantage_client.get_sentiment(ticker)
        sentiment_data["sources"]["alpha_vantage"] = av_data
    except Exception as e:
        logger.warning(f"Alpha Vantage failed for {ticker}: {e}")

    try:
        reddit_data = reddit_client.analyze_ticker(ticker)
        sentiment_data["sources"]["reddit"] = reddit_data
    except Exception as e:
        logger.warning(f"Reddit failed for {ticker}: {e}")

    # ... continue for other sources

    # If we have ANY data, calculate aggregate
    if sentiment_data["sources"]:
        sentiment_data = calculate_aggregate_sentiment(ticker, sentiment_data["sources"])
    else:
        logger.error(f"❌ ALL SOURCES FAILED for {ticker} - using neutral sentiment")

    return sentiment_data
```

### 7.2 Stale Data Detection

```python
def is_sentiment_data_stale() -> bool:
    """Check if sentiment data is too old."""
    sentiment_file = f"data/sentiment/{datetime.now().strftime('%Y-%m-%d')}.json"

    if not os.path.exists(sentiment_file):
        logger.warning("⚠️ No sentiment data for today - may be stale")
        return True

    # Check file modification time
    file_mtime = os.path.getmtime(sentiment_file)
    age_hours = (time.time() - file_mtime) / 3600

    if age_hours > 24:
        logger.warning(f"⚠️ Sentiment data is {age_hours:.1f} hours old - may be stale")
        return True

    return False
```

---

## 8. Implementation Timeline

### Phase 1: Core Infrastructure (Week 1)
- **Day 1-2**: Alpha Vantage + Reddit clients (4-5 hours)
- **Day 3**: Yahoo RSS + Finnhub clients (2 hours)
- **Day 4**: FRED + SEC clients (3-4 hours)
- **Day 5**: Sentiment aggregation + scoring logic (3 hours)
- **Day 6**: Storage implementation (JSON + history) (2 hours)
- **Day 7**: Testing + debugging (3 hours)

**Total**: ~20-25 hours (Week 1)

### Phase 2: Strategy Integration (Week 2)
- **Day 1**: CoreStrategy integration (2 hours)
- **Day 2**: GrowthStrategy integration (2 hours)
- **Day 3**: Error handling + fallbacks (3 hours)
- **Day 4**: Cron setup + automation (2 hours)
- **Day 5**: Testing with paper trading (3 hours)
- **Day 6-7**: Monitoring + refinement (4 hours)

**Total**: ~16 hours (Week 2)

### Phase 3: Optimization (Week 3+)
- SQLite migration (optional)
- Performance tuning
- Machine learning sentiment models (future)

---

## 9. Success Criteria

### Week 1 (Implementation)
- ✅ All 7 data sources integrated
- ✅ Daily sentiment JSON generated successfully
- ✅ Historical tracking functional
- ✅ Cron job runs without errors

### Week 2 (Integration)
- ✅ CoreStrategy uses sentiment for go/no-go decisions
- ✅ GrowthStrategy uses sentiment for scoring
- ✅ No trades executed during risk-off regimes
- ✅ Sentiment boosts technical scores correctly

### Month 1 (Validation)
- ✅ Sentiment data available 95%+ of trading days
- ✅ Improved win rate vs baseline (target: +5-10%)
- ✅ Reduced losses during bearish news cycles
- ✅ Better entry timing on bullish catalysts

---

## 10. Future Enhancements

### Phase 4: Advanced Features (Month 2+)

1. **Machine Learning Sentiment Models**
   - Train BERT model on historical news → sentiment correlation
   - Improve accuracy beyond keyword analysis

2. **Real-Time Sentiment Streaming**
   - WebSocket feeds for breaking news
   - Intraday sentiment updates (not just pre-market)

3. **Options Flow Integration**
   - Track unusual options activity (bullish/bearish bets)
   - Integrate with sentiment scoring

4. **Earnings Calendar Integration**
   - Automatically adjust sentiment around earnings dates
   - Avoid trades 1-2 days before earnings

5. **Correlation Analysis**
   - Track which sources predict market moves best
   - Dynamically adjust source weights based on accuracy

6. **Vector Database (ChromaDB)**
   - Store sentiment embeddings for semantic search
   - Query: "Find stocks with similar sentiment to NVDA in Nov 2025"

---

## 11. Key Decisions & Rationale

### Why JSON over SQLite initially?
- **Speed**: Get sentiment working in days, not weeks
- **Simplicity**: No schema migrations, easy to inspect/debug
- **Flexibility**: Easy to add new sources without ALTER TABLE
- **Upgrade Path**: Can migrate to SQLite once validated

### Why 7 sources?
- **Redundancy**: If 2-3 sources fail, still have consensus
- **Coverage**: News (Yahoo, Finnhub), Social (Reddit), AI (Alpha Vantage), Macro (FRED), Filings (SEC), Influencers (YouTube)
- **Free Tier**: All sources are 100% free, no cost scaling

### Why pre-market execution (8:00 AM)?
- **Timeliness**: Sentiment reflects overnight news + Asian markets
- **Buffer**: 1.5 hours to aggregate before 9:35 AM execution
- **Avoids Noise**: Pre-market is less volatile than market hours

### Why sentiment as filter (Tier 1) vs modifier (Tier 2)?
- **Tier 1 (SPY/QQQ/VOO)**: Low-risk → Conservative → Only trade on safe days
- **Tier 2 (NVDA/GOOGL/AMZN)**: Medium-risk → Opportunistic → Use sentiment to find best picks

---

## 12. Conclusion

This sentiment RAG system provides a **comprehensive, multi-source intelligence layer** for the trading system. By aggregating 7+ free data sources daily and storing them in a queryable format, we enable CoreStrategy and GrowthStrategy to make **better-informed, sentiment-aware decisions**.

**Key Benefits**:
1. **Risk Reduction**: Skip trades during risk-off regimes (VIX > 30)
2. **Better Timing**: Enter positions when sentiment is bullish
3. **YouTube Integration**: Leverage existing video analysis
4. **100% Free**: No additional costs
5. **Scalable**: Easy to add more sources or upgrade to SQLite

**Next Steps**:
1. CEO approval to proceed with Phase 1 implementation
2. Set up API keys for Alpha Vantage, Reddit, Finnhub, FRED
3. Begin Week 1 implementation (20-25 hours)
4. Test with paper trading before going live

**Estimated Impact on R&D Phase**:
- Win rate: +5-10% (from avoiding bad entries)
- Sharpe ratio: +0.3-0.5 (better risk-adjusted returns)
- Max drawdown: -2-3% (skip risk-off days)

---

## Appendix A: File Structure

```
trading/
├── data/
│   └── sentiment/
│       ├── 2025-11-09.json          # Daily sentiment scores
│       ├── 2025-11-10.json
│       └── history.json             # Historical tracking (90 days)
├── src/
│   ├── strategies/
│   │   ├── core_strategy.py         # Modified for sentiment filtering
│   │   └── growth_strategy.py       # Modified for sentiment scoring
│   └── utils/
│       ├── sentiment/
│       │   ├── alpha_vantage_client.py
│       │   ├── reddit_client.py
│       │   ├── yahoo_rss_parser.py
│       │   ├── finnhub_client.py
│       │   ├── fred_client.py
│       │   ├── sec_edgar_client.py
│       │   └── aggregator.py        # Main sentiment aggregation logic
│       └── sentiment_loader.py      # Helper for strategies to load sentiment
├── scripts/
│   └── sentiment_aggregator.py      # Cron job entry point (runs at 8 AM)
└── logs/
    └── sentiment.log                # Daily execution logs
```

---

## Appendix B: Environment Variables Required

```bash
# .env (add these)
ALPHA_VANTAGE_API_KEY=your_key_here
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
FINNHUB_API_KEY=your_key_here
FRED_API_KEY=your_key_here
```

**How to get keys** (all free):
1. **Alpha Vantage**: https://www.alphavantage.co/support/#api-key
2. **Reddit**: https://www.reddit.com/prefs/apps
3. **Finnhub**: https://finnhub.io/register
4. **FRED**: https://fred.stlouisfed.org/docs/api/api_key.html

---

**END OF DESIGN DOCUMENT**

*Generated by: CTO (Claude Agent)*
*Date: November 9, 2025*
*Version: 1.0*
*Status: Ready for CEO Review & Approval*
