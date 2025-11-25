---
skill_id: sentiment_analyzer
name: Sentiment Analyzer
version: 1.0.0
description: Analyzes market sentiment from multiple sources (news, social media, market indicators) for trading signals
author: Trading System CTO
tags: [sentiment, nlp, social-media, news-analysis, trading-signals]
tools:
  - analyze_news_sentiment
  - analyze_social_sentiment
  - get_composite_sentiment
  - detect_sentiment_anomalies
dependencies:
  - src/utils/news_sentiment.py
  - src/utils/sentiment_loader.py
  - src/utils/reddit_sentiment.py
  - src/rag/sentiment_store.py
integrations:
  - src/utils/news_sentiment.py::NewsSentimentAggregator
  - src/utils/sentiment_loader.py::load_latest_sentiment
---

# Sentiment Analyzer Skill

Multi-source sentiment analysis providing comprehensive market sentiment insights for trading decisions.

## Overview

This skill provides:
- News article sentiment scoring from multiple financial sources
- Social media sentiment aggregation (Twitter, Reddit, StockTwits)
- Market microstructure sentiment (order flow, volatility indicators)
- Composite sentiment scores with confidence intervals
- Trend detection and anomaly flagging
- Real-time sentiment monitoring

## Sentiment Scoring Methodology

### Score Range: -1.0 to +1.0
- **0.7 to 1.0**: Very Positive (Strong Buy Signal)
- **0.3 to 0.7**: Positive (Buy Signal)
- **-0.3 to 0.3**: Neutral (Hold)
- **-0.7 to -0.3**: Negative (Sell Signal)
- **-1.0 to -0.7**: Very Negative (Strong Sell Signal)

### Confidence Levels
- **High (>0.8)**: Strong agreement across sources
- **Medium (0.6-0.8)**: Moderate agreement
- **Low (<0.6)**: Mixed signals, use caution

## Tools

### 1. analyze_news_sentiment

Performs sentiment analysis on financial news articles.

**Parameters:**
- `symbols` (required): List of ticker symbols (e.g., ["AAPL", "MSFT"])
- `time_window_hours` (optional): Analysis window in hours (default: 24)
- `sources` (optional): Specific news sources to include (default: all available)

**Returns:**
```json
{
  "success": true,
  "sentiment": {
    "AAPL": {
      "overall_score": 0.72,
      "label": "positive",
      "confidence": 0.85,
      "article_count": 15,
      "breakdown": {
        "positive": 11,
        "neutral": 3,
        "negative": 1
      },
      "sources": {
        "yahoo": 0.75,
        "alphavantage": 0.68,
        "grok_twitter": 0.80
      },
      "trends": {
        "direction": "improving",
        "momentum": 0.12
      },
      "key_topics": [
        {"topic": "earnings", "sentiment": 0.85, "mentions": 8},
        {"topic": "product_launch", "sentiment": 0.70, "mentions": 5}
      ]
    }
  },
  "timestamp": "2025-11-25T10:00:00Z"
}
```

**Usage:**
```bash
python scripts/sentiment_analyzer.py analyze_news_sentiment --symbols AAPL MSFT --time-window-hours 24
```

### 2. analyze_social_sentiment

Aggregates sentiment from social media platforms.

**Parameters:**
- `symbols` (required): List of ticker symbols
- `platforms` (optional): Platforms to analyze (["twitter", "reddit", "stocktwits"], default: all)
- `time_window_hours` (optional): Analysis window (default: 6)
- `min_mentions` (optional): Minimum mention threshold (default: 10)

**Returns:**
```json
{
  "success": true,
  "sentiment": {
    "AAPL": {
      "overall_score": 0.65,
      "label": "positive",
      "confidence": 0.72,
      "total_mentions": 3420,
      "platforms": {
        "twitter": {
          "score": 0.68,
          "mentions": 1850,
          "trending": true
        },
        "reddit": {
          "score": 0.62,
          "mentions": 950,
          "trending": false
        },
        "stocktwits": {
          "score": 0.64,
          "mentions": 620,
          "trending": false
        }
      },
      "influencer_sentiment": 0.75,
      "retail_sentiment": 0.63,
      "volume_trend": "increasing",
      "anomalies": []
    }
  },
  "timestamp": "2025-11-25T10:00:00Z"
}
```

### 3. get_composite_sentiment

Generates weighted composite sentiment from all sources.

**Parameters:**
- `symbols` (required): List of ticker symbols
- `weights` (optional): Custom source weights object (default: balanced weights)
- `include_market_sentiment` (optional): Include technical indicators (default: true)

**Returns:**
```json
{
  "success": true,
  "composite_sentiment": {
    "AAPL": {
      "score": 0.68,
      "label": "positive",
      "confidence": 0.80,
      "components": {
        "news_sentiment": {
          "score": 0.72,
          "weight": 0.40,
          "contribution": 0.288
        },
        "social_sentiment": {
          "score": 0.65,
          "weight": 0.30,
          "contribution": 0.195
        },
        "market_sentiment": {
          "score": 0.70,
          "weight": 0.30,
          "contribution": 0.210
        }
      },
      "signal_strength": "strong",
      "recommendation": "buy",
      "risk_factors": [
        "High social media volatility",
        "Mixed sector sentiment"
      ]
    }
  },
  "timestamp": "2025-11-25T10:00:00Z"
}
```

### 4. detect_sentiment_anomalies

Identifies unusual sentiment patterns or rapid changes.

**Parameters:**
- `symbols` (required): List of ticker symbols
- `lookback_hours` (optional): Historical comparison window (default: 72)
- `sensitivity` (optional): "low", "medium", "high" (default: "medium")

**Returns:**
```json
{
  "success": true,
  "anomalies": [
    {
      "symbol": "AAPL",
      "type": "rapid_shift",
      "severity": "high",
      "description": "Sentiment shifted from 0.35 to 0.85 in 2 hours",
      "current_sentiment": 0.85,
      "previous_sentiment": 0.35,
      "trigger": "Breaking news: Positive earnings surprise",
      "recommendation": "Wait for stabilization before trading",
      "timestamp": "2025-11-25T09:30:00Z"
    }
  ]
}
```

## Data Sources

### News Sources (Priority Order)
1. Yahoo Finance News
2. Alpha Vantage News Sentiment
3. Grok Twitter (Real-time)
4. StockTwits
5. Reddit (r/wallstreetbets, r/stocks, r/investing)

### Social Media Platforms
1. Twitter/X (via Grok API)
2. Reddit (r/wallstreetbets, r/stocks, r/investing)
3. StockTwits

### Market Indicators
1. Put/Call Ratio
2. VIX (Fear Index)
3. Advance/Decline Line
4. On-Balance Volume (OBV)

## Integration with Trading System

This skill integrates with:
- `src/utils/news_sentiment.py` - NewsSentimentAggregator
- `src/utils/sentiment_loader.py` - Historical sentiment loading
- `src/rag/sentiment_store.py` - RAG-based sentiment storage
- `src/utils/reddit_sentiment.py` - Reddit sentiment analysis

## Rate Limiting & Caching

- News API: 100 requests/hour
- Social APIs: Variable by platform
- Results cached for 15 minutes
- Real-time updates for breaking news

## Usage Example

```python
from claude_skills import load_skill

sentiment_skill = load_skill("sentiment_analyzer")

# Get comprehensive sentiment before trade decision
composite = sentiment_skill.get_composite_sentiment(
    symbols=["AAPL"],
    include_market_sentiment=True
)

# Check for anomalies that might affect timing
anomalies = sentiment_skill.detect_sentiment_anomalies(
    symbols=["AAPL"],
    lookback_hours=24,
    sensitivity="high"
)

if composite["composite_sentiment"]["AAPL"]["score"] > 0.6 and not anomalies:
    print("Strong positive sentiment - consider buy")
```

## CLI Usage

```bash
# Analyze news sentiment
python scripts/sentiment_analyzer.py analyze_news_sentiment --symbols AAPL MSFT

# Get composite sentiment
python scripts/sentiment_analyzer.py get_composite_sentiment --symbols AAPL

# Detect anomalies
python scripts/sentiment_analyzer.py detect_sentiment_anomalies --symbols AAPL --sensitivity high
```

## Safety & Best Practices

- Always verify sentiment with multiple sources
- Consider confidence levels when making trading decisions
- Watch for sentiment anomalies that may indicate manipulation
- Combine sentiment with technical analysis for best results
- Cache results to avoid rate limiting

