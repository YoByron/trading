# Seeking Alpha Collector

Investment research article collector for Seeking Alpha using free RSS feeds.

## Overview

Seeking Alpha is a major investment research platform with analyst articles, ratings, and sentiment. This collector uses their free RSS feeds to gather investment research data without requiring API keys.

## Features

- **RSS Feed Access**: Uses free public RSS feeds (no API key required)
- **Sentiment Analysis**: Keyword-based bullish/bearish sentiment extraction
- **Analyst Ratings**: Infers ratings from article content (Strong Buy to Strong Sell)
- **Smart Caching**: 24-hour cache to respect rate limits and reduce API calls
- **Rate Limiting**: 2-second delay between requests
- **Recency Weighting**: More recent articles weighted higher in sentiment scoring

## Usage

### Basic Usage

```python
from src.rag.collectors.seekingalpha_collector import SeekingAlphaCollector

# Initialize collector
collector = SeekingAlphaCollector()

# Collect articles for a ticker
articles = collector.collect_ticker_news("NVDA", days_back=7)

# Get sentiment summary
summary = collector.get_ticker_summary("NVDA", days_back=7)
print(f"Sentiment: {summary['sentiment_score']}")
print(f"Article Count: {summary['article_count']}")
print(f"Avg Rating: {summary['avg_rating']}")
```

### Via Orchestrator

The collector is automatically included in the NewsOrchestrator:

```python
from src.rag.collectors.orchestrator import get_orchestrator

orchestrator = get_orchestrator()

# Seeking Alpha will be included in all news collection
articles = orchestrator.collect_all_ticker_news("NVDA", days_back=7)
```

### Command Line Interface

```bash
# Get summary for a ticker
python3 src/rag/collectors/seekingalpha_collector.py --ticker NVDA --summary --days 7

# Get full articles
python3 src/rag/collectors/seekingalpha_collector.py --ticker SPY --days 3

# Clear cache before fetching
python3 src/rag/collectors/seekingalpha_collector.py --ticker GOOGL --clear-cache
```

## Data Structure

### Article Format

Each article follows the base collector format with additional fields:

```python
{
    "title": "NVDA: Strong Buy Rating",
    "content": "Article summary...",
    "url": "https://seekingalpha.com/article/...",
    "published_date": "2025-11-29",
    "source": "seekingalpha",
    "ticker": "NVDA",
    "sentiment": 0.75,  # -1.0 to +1.0
    "rating": "Strong Buy",  # If detected in article
    "rating_score": 1.0,  # Normalized rating
    "collected_at": "2025-11-29T10:30:00"
}
```

### Summary Format

The `get_ticker_summary()` method returns:

```python
{
    "symbol": "NVDA",
    "sentiment_score": 0.65,  # Weighted by recency
    "article_count": 12,
    "avg_rating": 0.5,  # Average of all ratings
    "source": "seekingalpha",
    "ratings_breakdown": {
        "Strong Buy": 3,
        "Buy": 5,
        "Hold": 4
    },
    "recent_articles": [
        {
            "title": "...",
            "url": "...",
            "published_date": "...",
            "sentiment": 0.75,
            "rating": "Buy"
        }
    ]
}
```

## Sentiment Scoring

### Keywords

**Bullish Keywords** (positive sentiment):
- buy, bullish, upgrade, outperform, strong buy
- positive, growth, surge, rally, gain
- beat, strong, profit, rise, optimistic
- overweight, conviction buy, undervalued
- opportunity, momentum, breakout

**Bearish Keywords** (negative sentiment):
- sell, bearish, downgrade, underperform, strong sell
- negative, decline, drop, fall, miss
- weak, loss, crash, pessimistic, underweight
- overvalued, risk, warning, concern, headwind

### Rating Mapping

- **Strong Buy**: +1.0
- **Buy**: +0.5
- **Hold**: 0.0
- **Sell**: -0.5
- **Strong Sell**: -1.0

### Recency Weighting

Articles are weighted by recency using inverse index weighting:
- Most recent article: weight = 1.0
- Second article: weight = 0.5
- Third article: weight = 0.33
- And so on...

This ensures recent analyst opinions are weighted more heavily.

## Caching

### Cache Location

Cache files are stored in: `data/rag/cache/seekingalpha/`

### Cache Duration

24 hours (configurable via `CACHE_DURATION_HOURS`)

### Cache Management

```python
# Clear cache for specific ticker
collector = SeekingAlphaCollector()
cache_path = collector._get_cache_path("NVDA")
if cache_path.exists():
    cache_path.unlink()
```

## Rate Limiting

### Request Delay

2 seconds between requests (configurable via `REQUEST_DELAY_SECONDS`)

### Respectful Usage

- Uses free public RSS feeds
- Implements caching to minimize requests
- Rate limiting prevents server overload
- Follows robots.txt guidelines

## RSS Feed Format

Seeking Alpha provides free RSS feeds per ticker:

```
https://seekingalpha.com/api/sa/combined/{SYMBOL}.xml
```

Example: `https://seekingalpha.com/api/sa/combined/NVDA.xml`

The feed includes:
- Article titles
- Publication dates
- Article summaries
- Links to full articles
- Author information (in some feeds)

## Integration with Trading System

The collector integrates with the broader RAG (Retrieval-Augmented Generation) system:

1. **Data Collection**: Seeking Alpha articles collected daily
2. **Sentiment Analysis**: Aggregated with other sources (Yahoo, Reddit, Alpha Vantage)
3. **Trading Signals**: Used by RL agent for decision making
4. **Risk Assessment**: Helps validate trading opportunities

## Dependencies

- **feedparser**: RSS feed parsing (already in requirements.txt)
- **base_collector**: Abstract base class for collectors

## Error Handling

The collector handles common errors gracefully:

- **Feed parsing errors**: Returns empty list, logs warning
- **Network errors**: Retry with backoff (inherited from base class)
- **Invalid ticker**: Returns empty list
- **Rate limit exceeded**: Automatic delay between requests

## Testing

```bash
# Test with sample ticker
python3 src/rag/collectors/seekingalpha_collector.py --ticker SPY --summary

# Verify cache functionality
python3 src/rag/collectors/seekingalpha_collector.py --ticker NVDA --summary
python3 src/rag/collectors/seekingalpha_collector.py --ticker NVDA --summary  # Should use cache

# Clear cache and refetch
python3 src/rag/collectors/seekingalpha_collector.py --ticker NVDA --clear-cache --summary
```

## Future Enhancements

Potential improvements:

1. **Author Track Record**: Weight articles by author performance
2. **Article Categories**: Separate analysis vs news articles
3. **Price Target Extraction**: Parse price targets from articles
4. **Comments Sentiment**: Analyze article comments (requires web scraping)
5. **Premium API**: Upgrade to paid API for more features

## Notes

- Free RSS feeds have limited historical data (typically last 20-30 articles)
- For comprehensive historical analysis, consider Seeking Alpha's premium API
- RSS feeds may not include all article metadata (e.g., author ratings)
- Sentiment analysis is keyword-based and may not capture nuanced opinions

## References

- [Seeking Alpha](https://seekingalpha.com/)
- [RSS Feed Documentation](https://seekingalpha.com/page/api)
- [feedparser Documentation](https://feedparser.readthedocs.io/)
