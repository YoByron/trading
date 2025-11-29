# TikTok Sentiment Collector

Real-time sentiment analysis from TikTok financial content using the TikTok Research API.

## Overview

The TikTok sentiment collector monitors financial hashtags and extracts ticker mentions with sentiment scores from video captions. This provides insight into retail investor sentiment on one of the fastest-growing social platforms.

## Features

- OAuth2 authentication with TikTok Research API
- Searches financial hashtags: #stocks, #investing, #stocktok, #trading, #wallstreetbets
- Extracts ticker symbols from video descriptions ($TICKER format)
- Sentiment analysis using keyword matching (bullish/bearish indicators)
- Engagement scoring (weighted by likes, comments, shares, views)
- Rate limiting and error handling
- Integration with existing news collector infrastructure

## Setup

### 1. Get TikTok API Credentials

1. Create a TikTok Developer account at https://developers.tiktok.com/
2. Create a new app in the TikTok Developer Portal
3. Request access to the Research API (requires approval - may take 1-2 weeks)
4. Once approved, copy your Client Key and Client Secret

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# TikTok API (Research API for sentiment analysis)
TIKTOK_CLIENT_KEY=sbawkb0n3vpbo3jsxn
TIKTOK_CLIENT_SECRET=tQuSRw5q3QlV7vQ3Ccvyojeb7DQmb7W8
```

## Usage

### Standalone Usage

```python
from src.rag.collectors.tiktok_collector import TikTokCollector

# Initialize collector
collector = TikTokCollector()

# Get sentiment summary for a ticker
summary = collector.get_ticker_sentiment_summary(
    ticker="NVDA",
    days_back=7
)

print(summary)
# {
#     "symbol": "NVDA",
#     "sentiment_score": 0.72,  # 0-1 scale (0=bearish, 1=bullish)
#     "video_count": 15,
#     "engagement_score": 68.5,
#     "source": "tiktok",
#     "timestamp": "2025-11-29T10:30:00"
# }
```

### Collect Individual Videos

```python
# Collect videos mentioning specific ticker
videos = collector.collect_ticker_news(
    ticker="NVDA",
    days_back=7
)

for video in videos[:5]:
    print(f"Title: {video['title']}")
    print(f"Sentiment: {video['sentiment']:.2f}")
    print(f"Engagement: {video['engagement_score']:.2f}")
    print(f"Views: {video['view_count']:,}")
    print(f"URL: {video['url']}\n")
```

### Integrated with Orchestrator

The TikTok collector is automatically included in the News Orchestrator:

```python
from src.rag.collectors import get_orchestrator

# Get orchestrator (includes TikTok + Yahoo + Reddit + Alpha Vantage)
orchestrator = get_orchestrator()

# Collect all news for a ticker
all_news = orchestrator.collect_all_ticker_news(
    ticker="NVDA",
    days_back=7
)

# TikTok videos will be included in results
tiktok_videos = [
    article for article in all_news
    if article['source'] == 'tiktok'
]

print(f"Found {len(tiktok_videos)} TikTok videos")
```

### CLI Usage

Run directly from command line:

```bash
# Analyze ticker sentiment
python3 -m src.rag.collectors.tiktok_collector --ticker NVDA --days 7

# Collect general market videos
python3 -m src.rag.collectors.tiktok_collector --market --days 1
```

## Data Format

### Sentiment Summary

```python
{
    "symbol": "NVDA",
    "sentiment_score": 0.72,      # 0-1 scale (weighted by engagement)
    "video_count": 15,            # Number of videos analyzed
    "engagement_score": 68.5,     # Average engagement (0-100)
    "source": "tiktok",
    "timestamp": "2025-11-29T10:30:00"
}
```

### Individual Video Data

```python
{
    "title": "$NVDA to the moon! Strong buy signal 🚀📈",
    "content": "$NVDA to the moon! Strong buy signal 🚀📈",
    "url": "https://www.tiktok.com/@stocktrader123/video/7123456789",
    "published_date": "2025-11-29",
    "source": "tiktok",
    "ticker": "NVDA",
    "sentiment": 0.85,            # 0-1 scale
    "engagement_score": 75.2,     # Weighted engagement metric
    "video_id": "7123456789",
    "like_count": 1500,
    "comment_count": 250,
    "share_count": 100,
    "view_count": 50000,
    "hashtags": ["stocks", "investing", "NVDA"],
    "collected_at": "2025-11-29T10:30:00"
}
```

## Sentiment Analysis

### Keyword-Based Approach

The collector uses keyword matching for sentiment analysis:

**Bullish Keywords** (positive sentiment):
- buy, bullish, moon, rocket, gains, calls
- long, hold, breakout, rally, surge, pump
- strong, beating, upgrade, winning, profits

**Bearish Keywords** (negative sentiment):
- sell, bearish, crash, dump, puts, short
- drop, fall, decline, downgrade, losing
- weak, tank, plunge, recession, bubble

**Sentiment Score Calculation**:
```
sentiment = (bullish_count - bearish_count) / total_keywords
range: -1.0 (very bearish) to +1.0 (very bullish)
```

### Engagement Weighting

Videos with higher engagement have more influence on overall sentiment:

```python
engagement = (shares × 10 + comments × 5 + likes × 1) / views
engagement_score = min(engagement × 1000, 100)  # Normalized to 0-100
```

Final sentiment is weighted by engagement to prioritize viral content.

## Rate Limiting

TikTok Research API limits:
- **1,000 requests per day** (per app)
- **1 second delay** between requests (enforced by collector)

The collector automatically:
- Tracks request count
- Implements delays between API calls
- Caches OAuth2 tokens (2-hour expiry)
- Warns when approaching daily limit

## Error Handling

The collector gracefully handles:
- Missing API credentials (returns empty results)
- OAuth2 authentication failures (logs error, returns empty)
- API rate limits (backs off automatically)
- Network errors (retries with exponential backoff)
- Invalid ticker symbols (skips silently)
- Empty search results (returns empty list)

## TikTok Research API

### Authentication

Uses OAuth2 Client Credentials flow:
1. POST to `/v2/oauth/token/` with client_key + client_secret
2. Receive access_token (valid for 2 hours)
3. Use token in `Authorization: Bearer <token>` header

### Search Endpoint

```
POST https://open.tiktokapis.com/v2/research/video/query/
```

**Request Payload**:
```json
{
  "query": {
    "and": [
      {
        "field_name": "hashtag_name",
        "operation": "IN",
        "field_values": ["stocks"]
      }
    ]
  },
  "start_date": "20251122",
  "end_date": "20251129",
  "max_count": 20
}
```

**Response**:
```json
{
  "data": {
    "videos": [
      {
        "id": "7123456789",
        "video_description": "$NVDA to the moon!",
        "create_time": 1732876800,
        "username": "stocktrader123",
        "like_count": 1500,
        "comment_count": 250,
        "share_count": 100,
        "view_count": 50000,
        "hashtag_names": ["stocks", "NVDA"]
      }
    ]
  }
}
```

## Limitations

1. **Research API Access**: Requires manual approval from TikTok (can take 1-2 weeks)
2. **Rate Limits**: 1,000 requests/day limits data collection frequency
3. **Keyword-Based Sentiment**: Less sophisticated than LLM-based analysis
4. **Public Videos Only**: Cannot access private or restricted content
5. **Hashtag Dependency**: Only finds videos with financial hashtags
6. **Ticker Extraction**: Relies on $TICKER format (may miss unconventional mentions)

## Integration with Trading System

The TikTok collector integrates seamlessly with the existing RAG pipeline:

```python
# In your trading agent
from src.rag.collectors import get_orchestrator

orchestrator = get_orchestrator()

# Collect multi-source sentiment (including TikTok)
all_news = orchestrator.collect_all_ticker_news("NVDA", days_back=7)

# Aggregate sentiment across sources
tiktok_data = [a for a in all_news if a['source'] == 'tiktok']
avg_tiktok_sentiment = sum(v['sentiment'] for v in tiktok_data) / len(tiktok_data)

# Use in trading decision
if avg_tiktok_sentiment > 0.7 and len(tiktok_data) >= 10:
    print("Strong bullish TikTok sentiment detected!")
```

## Testing

Run the test suite:

```bash
# Run TikTok collector tests
pytest tests/test_tiktok_collector.py -v

# Test with coverage
pytest tests/test_tiktok_collector.py --cov=src.rag.collectors.tiktok_collector
```

## References

- [TikTok Research API Documentation](https://developers.tiktok.com/doc/research-api-overview)
- [TikTok OAuth2 Guide](https://developers.tiktok.com/doc/oauth-user-access-token-management)
- [TikTok Developer Portal](https://developers.tiktok.com/)

## Future Enhancements

1. **LLM-Based Sentiment**: Use OpenRouter to analyze video captions with GPT/Claude
2. **Video Transcription**: Analyze video transcripts (not just captions) for deeper insight
3. **Creator Influence**: Weight sentiment by creator follower count/credibility
4. **Trend Detection**: Identify emerging ticker mentions before they go viral
5. **Multi-Language Support**: Analyze non-English content for global sentiment
6. **Historical Tracking**: Store sentiment trends over time in database

---

**Created**: November 29, 2025
**Last Updated**: November 29, 2025
**Status**: Production Ready (pending API credentials approval)
