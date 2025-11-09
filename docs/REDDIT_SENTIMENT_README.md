# Reddit Sentiment Scraper

## Quick Reference

**File**: `src/utils/reddit_sentiment.py`
**Demo**: `src/utils/reddit_sentiment_demo.py`
**Setup Guide**: [reddit_sentiment_setup.md](reddit_sentiment_setup.md)
**Output**: `data/sentiment/reddit_YYYY-MM-DD.json`

## Overview

Production-ready Reddit sentiment scraper that collects daily sentiment from key investing subreddits to gauge retail investor sentiment and detect meme stock activity.

### Key Metrics
- **Subreddits Monitored**: 4 (r/wallstreetbets, r/stocks, r/investing, r/options)
- **Posts per Day**: ~100 (25 per subreddit)
- **Tickers Tracked**: ~20-50 per day
- **Cost**: $0 (100% FREE - Reddit API free tier)
- **Cache Duration**: 24 hours
- **Execution Time**: ~10 seconds

## Features

### 1. Sentiment Scoring Algorithm
- **Bullish Keywords**: +1 to +3 points (moon, rocket, calls, buy, etc)
- **Bearish Keywords**: -1 to -3 points (dump, crash, puts, sell, etc)
- **Engagement Weighting**: Logarithmic scaling by upvotes + comments
- **Confidence Levels**:
  - High: 10+ mentions, 100+ upvotes
  - Medium: 5+ mentions, 50+ upvotes
  - Low: <5 mentions or <50 upvotes

### 2. Ticker Extraction
- Pattern matching: `$SPY`, `NVDA`, `GOOGL`, etc.
- False positive filtering (excludes: CEO, IPO, DD, etc)
- Deduplication and validation

### 3. Data Collection
- Top 25 hot posts from each subreddit
- Last 24 hours time window
- Post metadata: title, text, upvotes, comments, flair
- Author, permalink, timestamp

### 4. Output Format

```json
{
  "meta": {
    "date": "2025-11-09",
    "total_posts": 100,
    "total_tickers": 45,
    "subreddit_stats": {...}
  },
  "sentiment_by_ticker": {
    "SPY": {
      "score": 127,
      "mentions": 45,
      "confidence": "high",
      "bullish_keywords": 67,
      "bearish_keywords": 12,
      "total_upvotes": 2340,
      "total_comments": 890,
      "avg_score_per_mention": 2.82,
      "top_posts": [...]
    }
  }
}
```

## Quick Start

### 1. Setup (One-time)

```bash
# Install dependencies
pip3 install praw --break-system-packages

# Create Reddit app (get credentials)
# https://www.reddit.com/prefs/apps

# Add to .env file
REDDIT_CLIENT_ID=your_14_char_client_id
REDDIT_CLIENT_SECRET=your_secret_key_here
REDDIT_USER_AGENT=TradingBot/1.0 by YourUsername
```

### 2. Run Demo (No credentials required)

```bash
python3 src/utils/reddit_sentiment_demo.py
```

### 3. Run Real Scraper

```bash
# Full scrape (all 4 subreddits)
python3 src/utils/reddit_sentiment.py

# Custom options
python3 src/utils/reddit_sentiment.py \
  --subreddits wallstreetbets,stocks \
  --limit 50 \
  --top 20 \
  --min-mentions 10
```

## Usage Examples

### Command Line

```bash
# Basic scrape
python3 src/utils/reddit_sentiment.py

# Force refresh (ignore cache)
python3 src/utils/reddit_sentiment.py --force-refresh

# Show top 20 tickers
python3 src/utils/reddit_sentiment.py --top 20

# Filter by minimum mentions
python3 src/utils/reddit_sentiment.py --min-mentions 10
```

### Programmatic

```python
from src.utils.reddit_sentiment import RedditSentiment

# Initialize
scraper = RedditSentiment()

# Collect sentiment (uses cache if <24h old)
data = scraper.collect_daily_sentiment()

# Get top bullish tickers
top = scraper.get_top_tickers(
    min_mentions=5,
    min_confidence='medium',
    limit=10
)

# Analyze specific ticker
spy = data['sentiment_by_ticker'].get('SPY')
print(f"SPY Sentiment: {spy['score']}")
```

### Integration with Trading System

```python
# Before market open (9:00 AM ET)
from src.utils.reddit_sentiment import RedditSentiment

scraper = RedditSentiment()
sentiment = scraper.collect_daily_sentiment()

# Get high-confidence bullish stocks
bullish = [
    ticker for ticker, data in sentiment['sentiment_by_ticker'].items()
    if data['score'] > 50
    and data['confidence'] == 'high'
    and data['mentions'] >= 10
]

# Avoid high-confidence bearish stocks
bearish = [
    ticker for ticker, data in sentiment['sentiment_by_ticker'].items()
    if data['score'] < -30
    and data['confidence'] == 'high'
]

# Use in Tier 2 strategy
# Boost technical score for bullish sentiment
# Reduce score for bearish sentiment
```

## Output Structure

### Meta Information
- `date`: YYYY-MM-DD
- `timestamp`: ISO 8601 format
- `total_posts`: Total posts analyzed
- `total_tickers`: Unique tickers found
- `subreddit_stats`: Per-subreddit collection stats

### Ticker Data
- `score`: Total sentiment score (positive = bullish, negative = bearish)
- `mentions`: Number of times ticker was mentioned
- `confidence`: high/medium/low (based on mentions + engagement)
- `bullish_keywords`: Count of bullish keywords
- `bearish_keywords`: Count of bearish keywords
- `total_upvotes`: Sum of upvotes across all posts
- `total_comments`: Sum of comments across all posts
- `avg_score_per_mention`: Score normalized by mentions
- `top_posts`: Top 3 posts by sentiment score (with permalinks)

## Interpretation Guide

### Bullish Signals (Consider buying)
- **Score > 50** with **high confidence** = Strong bullish sentiment
- **Mentions > 20** with **rising engagement** = Popular stock
- **Bullish keywords > 2x bearish** = Clear positive sentiment
- **Flairs: DD, Discussion, Gain** = Thoughtful analysis or success stories

### Bearish Signals (Avoid or short)
- **Score < -30** with **high confidence** = Strong bearish sentiment
- **Mentions > 20** with **flairs: Loss, YOLO** = Potential bag holders
- **Bearish keywords > 2x bullish** = Clear negative sentiment

### Meme Stock Alerts (High volatility risk)
- **Mentions > 30** with **flair: YOLO** = Pump potential (volatile)
- **Sudden spike in mentions** = FOMO risk
- **High upvotes but low comments** = Potential brigading

### Neutral/Ignore
- **Score < 20 and > -20** = No clear sentiment
- **Confidence: low** = Not enough data
- **Mentions < 5** = Too few to be reliable

## Caching & Performance

### Cache Strategy
- **Duration**: 24 hours
- **Location**: `data/sentiment/reddit_YYYY-MM-DD.json`
- **Invalidation**: Automatic after 24 hours
- **Force Refresh**: `--force-refresh` flag

### Performance
- **Execution Time**: ~10 seconds (4 subreddits, 25 posts each)
- **API Calls**: 4-8 requests (well within 100/min limit)
- **Memory**: <50MB
- **Cache Size**: ~5-10KB per day

## Error Handling

### Retry Logic
- 3 attempts with exponential backoff (2s, 4s, 8s)
- Graceful failures (continues if one subreddit fails)
- Comprehensive logging

### Common Errors

**401 HTTP Response**
- Cause: Missing or invalid Reddit API credentials
- Fix: Check .env file, verify credentials at reddit.com/prefs/apps

**Rate Limit**
- Cause: Too many requests (>100/min)
- Fix: Reduce --limit, add delays, use caching

**No Tickers Found**
- Cause: Time filter too restrictive or inactive subreddit
- Fix: Increase --limit, check subreddit activity

## Monitoring

### Daily Check
```bash
# View latest data
cat data/sentiment/reddit_$(date +%Y-%m-%d).json | jq '.meta'

# Count tickers
cat data/sentiment/reddit_*.json | jq '.sentiment_by_ticker | length'

# Top 5 by score
cat data/sentiment/reddit_*.json | jq '.sentiment_by_ticker | to_entries | sort_by(.value.score) | reverse | .[0:5]'
```

### Integration with Daily Report
```python
# Add to daily CEO report
sentiment = scraper.collect_daily_sentiment()
report += "\n## Reddit Sentiment (Top 10)\n"

for ticker, data in scraper.get_top_tickers(limit=10):
    direction = "📈" if data['score'] > 0 else "📉"
    report += f"- {ticker}: {data['score']} ({data['mentions']} mentions) {direction}\n"
```

## Automation

### Schedule with Cron
```bash
# Run daily at 8:30 AM ET (before market open)
30 8 * * 1-5 cd /path/to/trading && python3 src/utils/reddit_sentiment.py
```

### Integrate with main.py
```python
# At start of daily execution
from src.utils.reddit_sentiment import RedditSentiment

logger.info("Collecting Reddit sentiment...")
scraper = RedditSentiment()
sentiment = scraper.collect_daily_sentiment()
```

## Cost & Limits

### FREE Tier (Reddit API)
- **API Calls**: 100/minute, 1000/hour
- **Cost**: $0
- **Requirements**: Reddit app credentials (free)

### This Scraper's Usage
- **API Calls**: 4-8 per execution
- **Frequency**: Once per day (recommended)
- **Well Within Limits**: Yes (4 calls vs 100/min limit)

## Future Enhancements

### Phase 1 (When profitable)
- [ ] Real-time monitoring (intraday updates every hour)
- [ ] Alert system for sudden sentiment shifts (>50% change)
- [ ] Integration with MultiLLMAnalyzer for deeper analysis

### Phase 2 (Month 4+)
- [ ] Historical sentiment tracking (30-day trends)
- [ ] Sentiment-price correlation analysis
- [ ] Meme stock detector (auto-flag high-risk YOLOs)

### Phase 3 (Month 6+)
- [ ] ML model: Predict price movement from sentiment
- [ ] Sentiment momentum (is sentiment accelerating?)
- [ ] Cross-platform sentiment (Twitter, StockTwits, Discord)

## Troubleshooting

See [reddit_sentiment_setup.md](reddit_sentiment_setup.md) for detailed troubleshooting.

## References

- **Setup Guide**: [reddit_sentiment_setup.md](reddit_sentiment_setup.md)
- **PRAW Docs**: https://praw.readthedocs.io/
- **Reddit API**: https://www.reddit.com/dev/api/
- **Create App**: https://www.reddit.com/prefs/apps

## Support

For issues:
1. Check logs: `logs/trading_*.log`
2. Verify credentials in `.env`
3. Test with demo: `python3 src/utils/reddit_sentiment_demo.py`
4. Check Reddit API status: https://www.redditstatus.com/

---

**Status**: ✅ Production Ready
**Cost**: $0 (FREE)
**Maintenance**: Zero (after setup)
**Recommended Schedule**: Daily at 8:30 AM ET
