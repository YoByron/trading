# LinkedIn Sentiment Collector - Usage Guide

## Overview

The LinkedIn Sentiment Collector fetches professional financial content from LinkedIn to gauge institutional and professional investor sentiment.

**File Location**: `/Users/igorganapolsky/workspace/git/apps/trading/src/rag/collectors/linkedin_collector.py`

## Features

- OAuth2 authentication with LinkedIn API
- Search for posts containing stock tickers ($SPY, $QQQ, etc.)
- Professional sentiment analysis (bullish/bearish/neutral)
- Rate limiting (500 requests/day on free tier)
- 24-hour caching
- Engagement-weighted sentiment scoring
- Structured output format

## Setup Instructions

### 1. Create LinkedIn App

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Click "Create app"
3. Fill in app details:
   - App name: "Trading Sentiment Analyzer"
   - Company: Your company name
   - Privacy policy URL: (required)
   - App logo: (optional)
4. Click "Create app"

### 2. Request API Access

1. In your app dashboard, go to "Products"
2. Request access to:
   - **Marketing Developer Platform** (recommended)
   - OR **Share on LinkedIn** + **Sign In with LinkedIn**
3. Wait for approval (usually 1-3 business days)

### 3. Configure OAuth2

1. Go to "Auth" tab in your app
2. Add OAuth 2.0 redirect URLs:
   - `http://localhost:8080/callback` (for development)
   - Your production callback URL
3. Note your credentials:
   - **Client ID**: Found on Auth tab
   - **Client Secret**: Found on Auth tab (keep secure!)

### 4. Add Credentials to .env

```bash
# LinkedIn API credentials
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_ACCESS_TOKEN=  # Optional - will be generated via OAuth2
```

### 5. Generate Access Token (Optional)

For automated scripts, you can pre-generate an access token:

```bash
# Manual OAuth2 flow (simplified)
# 1. Visit authorization URL:
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=r_liteprofile%20r_emailaddress%20w_member_social

# 2. Authorize and get code from redirect
# 3. Exchange code for token:
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -d grant_type=authorization_code \
  -d code=YOUR_AUTH_CODE \
  -d redirect_uri=YOUR_REDIRECT_URI \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET

# 4. Copy access_token and add to .env
```

## Usage

### Command Line

```bash
# Analyze specific tickers
python src/rag/collectors/linkedin_collector.py --tickers SPY,QQQ,NVDA

# Custom lookback period
python src/rag/collectors/linkedin_collector.py --tickers AAPL --days 14

# Save to custom file
python src/rag/collectors/linkedin_collector.py --tickers TSLA --output data/linkedin_tesla.json
```

### Programmatic Usage

```python
from src.rag.collectors.linkedin_collector import LinkedInCollector

# Initialize collector
collector = LinkedInCollector()

# Analyze single ticker
sentiment = collector.analyze_ticker_sentiment("SPY")
print(f"SPY Sentiment: {sentiment['sentiment_score']:.2f}")
print(f"Post Count: {sentiment['post_count']}")
print(f"Confidence: {sentiment['confidence']}")

# Collect posts for ticker
posts = collector.collect_ticker_news("NVDA", days_back=7)
for post in posts:
    print(f"- {post['title']}")
    print(f"  Sentiment: {post['sentiment']:.2f}")

# Collect market news (uses SPY as proxy)
market_posts = collector.collect_market_news(days_back=3)
```

### Integration with RAG System

```python
from src.rag.collectors import LinkedInCollector

# Initialize collector
linkedin = LinkedInCollector()

# Collect ticker news
articles = linkedin.collect_ticker_news("TSLA", days_back=7)

# Save to RAG store (optional)
linkedin.save_raw(articles, ticker="TSLA")
```

## Output Format

### Sentiment Analysis

```json
{
  "symbol": "SPY",
  "sentiment_score": 0.65,
  "post_count": 15,
  "source": "linkedin",
  "bullish_signals": 10,
  "bearish_signals": 5,
  "confidence": "medium"
}
```

### Normalized Articles

```json
{
  "title": "SPY breaks through resistance...",
  "content": "Full post text here...",
  "url": "https://linkedin.com/feed/update/...",
  "published_date": "2025-11-29",
  "source": "linkedin",
  "ticker": "SPY",
  "sentiment": 0.72,
  "collected_at": "2025-11-29T10:30:00"
}
```

## Sentiment Scoring Algorithm

The LinkedIn collector uses a professional sentiment scoring system:

### Bullish Keywords (Professional Tone)
- **Strong Bullish** (+2 to +3): "strong buy", "outperform", "upgrade", "breakout"
- **Moderate Bullish** (+1): "positive", "growth", "opportunity", "improving"

### Bearish Keywords (Professional Tone)
- **Strong Bearish** (-2 to -3): "sell", "downgrade", "collapse", "plunge"
- **Moderate Bearish** (-1): "risk", "concern", "weak", "challenging"

### Engagement Weighting
- Reactions: Log-weighted (likes, etc.)
- Comments: 1.5x weight (higher engagement)
- Shares: 2x weight (highest signal)

Formula:
```
base_score = (bullish_keywords - bearish_keywords)
engagement_weight = (log(reactions) + 1.5*log(comments) + 2*log(shares)) / 3
final_score = base_score * engagement_weight
normalized_sentiment = (final_score + 100) / 200  # Scale to 0-1
```

## Rate Limiting

- **Free Tier**: 500 requests/day
- **Minimum Interval**: ~172 seconds between requests
- **Auto-throttling**: Built-in rate limiting
- **Caching**: 24-hour cache reduces API calls

## Error Handling

The collector includes robust error handling:

```python
try:
    collector = LinkedInCollector()
    sentiment = collector.analyze_ticker_sentiment("SPY")
except ValueError as e:
    print(f"Configuration error: {e}")
    # Missing credentials
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed - token expired")
    elif e.response.status_code == 429:
        print("Rate limit exceeded - wait 24 hours")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Caching

- **Location**: `data/sentiment/linkedin_TICKER_YYYY-MM-DD.json`
- **TTL**: 24 hours (configurable)
- **Force Refresh**: Delete cache file or pass `force_refresh=True`

## Comparison with Reddit Collector

| Feature | LinkedIn | Reddit |
|---------|----------|--------|
| **Tone** | Professional | Retail/Casual |
| **Sentiment** | Institutional | Retail |
| **Keywords** | Formal (upgrade, outperform) | Informal (moon, rocket) |
| **Engagement** | Reactions, shares | Upvotes, comments |
| **Rate Limit** | 500/day | 100/min |
| **Best For** | Long-term analysis | Short-term trends |

## Integration Example

```python
from src.rag.collectors import LinkedInCollector, RedditCollector

# Combine professional + retail sentiment
linkedin = LinkedInCollector()
reddit = RedditCollector()

ticker = "NVDA"

# Get both perspectives
professional = linkedin.analyze_ticker_sentiment(ticker)
retail = reddit.collect_ticker_news(ticker)

# Weighted average (60% professional, 40% retail)
combined_sentiment = (
    0.6 * professional['sentiment_score'] +
    0.4 * (retail['overall_sentiment'] if retail else 0.5)
)

print(f"Combined sentiment for {ticker}: {combined_sentiment:.2f}")
```

## Troubleshooting

### "No LinkedIn API credentials provided"
- Add `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` to `.env`
- Verify credentials are correct

### "Authentication failed"
- Access token expired (generate new one)
- Invalid credentials (check LinkedIn app dashboard)

### "Rate limit exceeded"
- Wait 24 hours for reset
- Implement longer caching
- Use multiple apps with different credentials (not recommended)

### "Marketing Developer Platform access required"
- Request access in LinkedIn app dashboard
- Wait for approval (1-3 business days)
- Use alternative APIs if available

## API Limitations

### Free Tier Restrictions
- 500 requests/day
- Limited search capabilities
- No historical data (last 30 days only)

### Marketing Developer Platform
- Higher rate limits
- Better search API
- More data access
- Requires approval

### Paid Plans
- Enterprise API access
- Unlimited requests
- Historical data
- Priority support

## Next Steps

1. Set up LinkedIn app credentials
2. Test with CLI: `python src/rag/collectors/linkedin_collector.py --tickers SPY`
3. Integrate with RAG pipeline
4. Combine with Reddit for multi-source sentiment
5. Monitor rate limits and adjust caching

## Support

- LinkedIn Developer Docs: https://docs.microsoft.com/en-us/linkedin/
- API Support: https://www.linkedin.com/help/linkedin/ask/api
- Rate Limits: https://docs.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits
