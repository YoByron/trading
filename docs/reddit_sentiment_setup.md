# Reddit Sentiment Scraper - Setup Guide

## Overview

The Reddit Sentiment Scraper collects daily sentiment from key investing subreddits to gauge retail investor sentiment and detect meme stock activity. It runs BEFORE market open (9:35 AM ET) to inform trading decisions.

**File Location**: `src/utils/reddit_sentiment.py`

## Features

### Monitored Subreddits
- **r/wallstreetbets**: Meme stocks, YOLO plays, gain/loss porn
- **r/stocks**: General market discussion
- **r/investing**: Long-term investment talk
- **r/options**: Derivatives sentiment

### Data Extracted
- Top 25 posts from each subreddit (hot + rising)
- Ticker mentions (e.g., $SPY, NVDA, GOOGL)
- Sentiment indicators:
  - Upvote ratio
  - Number of comments (engagement)
  - Post flair (DD, Discussion, YOLO, Loss, Gain)
  - Bullish/bearish keywords
  - Time window: Last 24 hours

### Sentiment Scoring Algorithm

**Base Score**:
- Bullish keywords: +1 to +3 points each
  - Strong: "moon", "rocket", "diamond hands" (+3)
  - Medium: "calls", "buy", "bullish" (+2)
  - Weak: "hold", "green", "up" (+1)

- Bearish keywords: -1 to -3 points each
  - Strong: "dump", "crash", "collapse" (-3)
  - Medium: "puts", "sell", "bearish" (-2)
  - Weak: "down", "red" (-1)

**Weighting**:
- Weighted by upvotes (logarithmic scaling)
- Weighted by comments (high engagement = more reliable)
- Final score = base_score × engagement_weight

**Confidence Levels**:
- **High**: 10+ mentions, 100+ upvotes
- **Medium**: 5+ mentions, 50+ upvotes
- **Low**: < 5 mentions or < 50 upvotes

### Output Format

```json
{
  "meta": {
    "date": "2025-11-09",
    "timestamp": "2025-11-09T09:00:00",
    "subreddits": ["wallstreetbets", "stocks", "investing", "options"],
    "total_posts": 100,
    "total_tickers": 45
  },
  "sentiment_by_ticker": {
    "SPY": {
      "score": 75,
      "mentions": 142,
      "confidence": "high",
      "bullish_keywords": 89,
      "bearish_keywords": 12,
      "total_upvotes": 1250,
      "total_comments": 450,
      "avg_score_per_mention": 0.53,
      "top_posts": [...]
    }
  }
}
```

**File Output**: `data/sentiment/reddit_YYYY-MM-DD.json`

## Setup Instructions

### Step 1: Create Reddit App

1. Go to: https://www.reddit.com/prefs/apps
2. Scroll to bottom and click **"create app"** or **"create another app"**
3. Fill in details:
   - **Name**: TradingBot (or any name)
   - **App type**: Select **"script"**
   - **Description**: Automated trading sentiment analysis
   - **About URL**: (leave blank or use your GitHub)
   - **Redirect URI**: http://localhost:8080 (required but not used)
4. Click **"create app"**
5. You'll see:
   - **client_id**: 14-character string under the app name
   - **secret**: Longer string labeled "secret"

### Step 2: Add Credentials to .env

Add these lines to `/Users/igorganapolsky/workspace/git/apps/trading/.env`:

```bash
# Reddit API (for sentiment analysis)
REDDIT_CLIENT_ID=your_14_char_client_id
REDDIT_CLIENT_SECRET=your_secret_key_here
REDDIT_USER_AGENT=TradingBot/1.0 by YourRedditUsername
```

**Important**: Replace `YourRedditUsername` with your actual Reddit username.

### Step 3: Install Dependencies

```bash
pip3 install praw --break-system-packages
```

(Already installed in this project)

### Step 4: Test the Scraper

```bash
# Test with single subreddit
python3 src/utils/reddit_sentiment.py --subreddits wallstreetbets --limit 10

# Full scrape (all 4 subreddits)
python3 src/utils/reddit_sentiment.py

# Force refresh (ignore cache)
python3 src/utils/reddit_sentiment.py --force-refresh
```

## Usage Examples

### Command Line

```bash
# Scrape all subreddits (25 posts each)
python3 src/utils/reddit_sentiment.py

# Scrape specific subreddits
python3 src/utils/reddit_sentiment.py --subreddits wallstreetbets,stocks --limit 50

# Show top 20 tickers with at least 10 mentions
python3 src/utils/reddit_sentiment.py --top 20 --min-mentions 10

# Force refresh and show top 5
python3 src/utils/reddit_sentiment.py --force-refresh --top 5
```

### Programmatic Usage

```python
from src.utils.reddit_sentiment import RedditSentiment

# Initialize scraper
scraper = RedditSentiment()

# Collect daily sentiment (uses cache if < 24 hours old)
sentiment_data = scraper.collect_daily_sentiment()

# Get top tickers
top_tickers = scraper.get_top_tickers(
    min_mentions=5,
    min_confidence='medium',
    limit=10
)

# Analyze specific ticker
spy_data = sentiment_data['sentiment_by_ticker'].get('SPY')
if spy_data:
    print(f"SPY Sentiment: {spy_data['score']}")
    print(f"Mentions: {spy_data['mentions']}")
    print(f"Confidence: {spy_data['confidence']}")
```

### Integration with Trading System

```python
# In core strategy (before market open)
from src.utils.reddit_sentiment import RedditSentiment

scraper = RedditSentiment()
sentiment = scraper.collect_daily_sentiment()

# Get bullish stocks with high confidence
bullish_tickers = [
    ticker for ticker, data in sentiment['sentiment_by_ticker'].items()
    if data['score'] > 50  # Bullish
    and data['confidence'] == 'high'  # High confidence
    and data['mentions'] >= 10  # Popular
]

# Avoid bearish stocks
bearish_tickers = [
    ticker for ticker, data in sentiment['sentiment_by_ticker'].items()
    if data['score'] < -30  # Bearish
    and data['confidence'] == 'high'
]

# Use in Tier 2 strategy (Growth stocks)
# Boost score for bullish Reddit sentiment
# Reduce score for bearish Reddit sentiment
```

## Caching

- Results cached for **24 hours** by default
- Cache location: `data/sentiment/reddit_YYYY-MM-DD.json`
- Use `--force-refresh` to bypass cache
- Cache automatically refreshed if older than 24 hours

## Rate Limits

**Reddit API (Free Tier)**:
- 100 requests per minute
- 1000 requests per hour
- This scraper uses ~4-8 requests (well within limits)

**Best Practices**:
- Run once per day (before market open)
- Use caching to avoid redundant API calls
- Monitor for rate limit errors

## Error Handling

The scraper includes:
- **Retry logic**: 3 attempts with exponential backoff
- **Graceful failures**: Continues if one subreddit fails
- **Comprehensive logging**: All errors logged with context
- **Validation**: Filters out false positive tickers

## Monitoring

### Check Scraper Status

```bash
# View latest sentiment data
cat data/sentiment/reddit_2025-11-09.json | jq '.meta'

# Count tickers found
cat data/sentiment/reddit_2025-11-09.json | jq '.sentiment_by_ticker | length'

# Top 5 tickers by score
cat data/sentiment/reddit_2025-11-09.json | jq '.sentiment_by_ticker | to_entries | sort_by(.value.score) | reverse | .[0:5]'
```

### Add to Daily Reporting

```python
# In daily_report.py or autonomous_trader.py
from src.utils.reddit_sentiment import RedditSentiment

scraper = RedditSentiment()
sentiment = scraper.collect_daily_sentiment()

# Add to report
report += "\n## Reddit Sentiment (Top 10)\n"
top = scraper.get_top_tickers(limit=10)
for ticker, data in top:
    direction = "📈 BULLISH" if data['score'] > 0 else "📉 BEARISH"
    report += f"- {ticker}: {data['score']} ({data['mentions']} mentions, {data['confidence']} confidence) {direction}\n"
```

## Automation

### Schedule Daily Scraping (Before Market Open)

Add a lightweight GitHub Actions workflow (`reddit-sentiment.yml`) that runs at 8:30 AM ET and executes `python3 src/utils/reddit_sentiment.py`. This ensures sentiment data is gathered before the main trading workflow. Alternatively integrate directly into `main.py`:

```python
# At start of daily execution
from src.utils.reddit_sentiment import RedditSentiment

logger.info("Collecting Reddit sentiment...")
scraper = RedditSentiment()
sentiment = scraper.collect_daily_sentiment()
logger.info(f"Found {len(sentiment['sentiment_by_ticker'])} tickers with sentiment data")
```

## Cost

**FREE** - Uses Reddit API free tier:
- No API fees
- Unlimited read-only access
- 100 requests/minute (more than enough)

## Future Enhancements

### Phase 1 (When profitable)
- Integration with MultiLLMAnalyzer for deeper sentiment analysis
- Real-time monitoring (intraday updates)
- Alert system for sudden sentiment shifts

### Phase 2 (Month 4+)
- Historical sentiment tracking (correlate with price movements)
- Meme stock detector (flag YOLOs before they pump)
- Sentiment divergence alerts (Reddit loves it, analysts hate it)

### Phase 3 (Month 6+)
- ML model: Predict price movement from sentiment
- Sentiment momentum (is sentiment accelerating?)
- Cross-platform sentiment (Twitter, StockTwits, Discord)

## Troubleshooting

### Error: "401 HTTP response"
- Reddit API credentials missing or invalid
- Check .env file has correct REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
- Verify credentials at https://www.reddit.com/prefs/apps

### Error: "ModuleNotFoundError: No module named 'praw'"
- Install praw: `pip3 install praw --break-system-packages`

### No tickers found
- Check if posts are < 24 hours old (time_filter='day')
- Try increasing --limit (default: 25)
- Check subreddit is active (r/wallstreetbets always has activity)

### Rate limit errors
- Reduce --limit per subreddit
- Add delay between requests
- Use caching to avoid redundant calls

## Support

For issues or questions:
1. Check logs: `logs/trading_*.log`
2. Verify .env credentials
3. Test with single subreddit first
4. Check Reddit API status: https://www.redditstatus.com/

## References

- PRAW Documentation: https://praw.readthedocs.io/
- Reddit API: https://www.reddit.com/dev/api/
- Create Reddit App: https://www.reddit.com/prefs/apps
