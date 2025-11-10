# News Sentiment Aggregator

Multi-source financial news sentiment analysis system that aggregates professional analyst sentiment and social trading sentiment for pre-market trading decisions.

## Features

### 3 Data Sources

1. **Yahoo Finance** (via yfinance)
   - News headlines and articles
   - Keyword-based sentiment analysis
   - Free, unlimited access
   - No API key required

2. **Stocktwits API**
   - Social trading sentiment
   - Bullish/Bearish labels from retail traders
   - 200 requests/hour (free tier)
   - No API key required

3. **Alpha Vantage News Sentiment**
   - AI-powered sentiment scores
   - Professional news sources
   - Relevance-weighted analysis
   - 25 requests/day (free tier)
   - **API key required** (free)

### Weighted Aggregation

Sentiment scores are combined using these weights:
- **Alpha Vantage**: 40% (most reliable, AI-powered)
- **Stocktwits**: 30% (retail trader sentiment)
- **Yahoo Finance**: 30% (news headline analysis)

### Output Format

```json
{
  "meta": {
    "date": "2025-11-09",
    "timestamp": "2025-11-09T09:30:00",
    "sources": ["yahoo", "stocktwits", "alphavantage"],
    "tickers_analyzed": 6
  },
  "sentiment_by_ticker": {
    "SPY": {
      "ticker": "SPY",
      "score": 65.0,
      "confidence": "high",
      "sources": {
        "yahoo": {"score": 70, "articles": 12},
        "stocktwits": {"score": 55, "messages": 234, "bullish": 150, "bearish": 84},
        "alphavantage": {"score": 75, "relevance": 0.9, "articles": 15}
      },
      "timestamp": "2025-11-09T09:30:00"
    }
  }
}
```

## Installation

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install alpha-vantage requests yfinance
```

Already added to `requirements.txt`:
```
alpha-vantage==2.3.1
```

### 2. Get Alpha Vantage API Key (Required)

**Free tier**: 25 requests/day (sufficient for pre-market analysis)

1. Go to: https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Copy the API key
4. Add to `.env`:

```bash
ALPHA_VANTAGE_API_KEY=your_key_here
```

## Usage

### Command Line Interface

#### Analyze Multiple Tickers
```bash
# Analyze default watchlist (SPY, QQQ, VOO, NVDA, GOOGL, AMZN)
python3 -m src.utils.news_sentiment

# Analyze custom tickers
python3 -m src.utils.news_sentiment --tickers "AAPL,MSFT,TSLA"
```

#### Test with Single Ticker
```bash
python3 -m src.utils.news_sentiment --test
```

#### Load Previous Report
```bash
python3 -m src.utils.news_sentiment --load news_2025-11-09.json
```

### Python Integration

```python
from src.utils.news_sentiment import NewsSentimentAggregator

# Initialize aggregator
aggregator = NewsSentimentAggregator()

# Analyze tickers
watchlist = ["SPY", "QQQ", "VOO", "NVDA", "GOOGL", "AMZN"]
report = aggregator.analyze_tickers(watchlist)

# Print summary
aggregator.print_summary(report)

# Save to file
filepath = aggregator.save_report(report)
print(f"Report saved to: {filepath}")
```

### Integration with Trading Strategy

```python
# Pre-market sentiment analysis
report = aggregator.analyze_tickers(watchlist)

for ticker, sentiment in report.sentiment_by_ticker.items():
    score = sentiment.score
    confidence = sentiment.confidence

    # Strong bullish signal
    if score > 60 and confidence == "high":
        print(f"STRONG BUY: {ticker} (sentiment: {score:+.1f})")
        # Increase position size or add to buy list

    # Strong bearish signal
    elif score < -60 and confidence == "high":
        print(f"STRONG SELL: {ticker} (sentiment: {score:+.1f})")
        # Reduce position size or add to avoid list

    # Neutral
    elif abs(score) < 20:
        print(f"NEUTRAL: {ticker} (sentiment: {score:+.1f})")
        # Use other signals (momentum, RL agent)
```

## Sentiment Scoring

### Score Range: -100 to +100

- **+60 to +100**: Strong Bullish (buy signal)
- **+20 to +60**: Bullish (positive sentiment)
- **-20 to +20**: Neutral (no clear direction)
- **-60 to -20**: Bearish (negative sentiment)
- **-100 to -60**: Strong Bearish (sell signal)

### Confidence Levels

- **High**: 10+ articles/messages from multiple sources
- **Medium**: 5-10 articles/messages, or 1-2 sources
- **Low**: <5 articles/messages, or single source

## API Details

### Yahoo Finance
- **Library**: yfinance
- **Cost**: Free
- **Rate Limit**: None (reasonable use)
- **Data**: News headlines, timestamps
- **Sentiment**: Keyword matching (bullish/bearish keywords)

### Stocktwits
- **Endpoint**: `https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json`
- **Cost**: Free
- **Rate Limit**: 200 requests/hour
- **Data**: User messages, sentiment labels (Bullish/Bearish/Neutral)
- **Sentiment**: Aggregated user sentiment

### Alpha Vantage
- **Endpoint**: `https://www.alphavantage.co/query?function=NEWS_SENTIMENT`
- **Cost**: Free tier (25 calls/day)
- **Rate Limit**: 25 requests/day (free), 75/day (premium $50/mo)
- **Data**: News articles, AI sentiment scores, relevance scores
- **Sentiment**: AI-powered analysis (-1 to +1, scaled to -100 to +100)

## File Structure

```
trading/
├── src/utils/
│   └── news_sentiment.py          # Main module
├── data/sentiment/
│   ├── news_2025-11-09.json      # Daily sentiment reports
│   └── news_2025-11-10.json
├── test_sentiment_demo.py         # Demo script
└── docs/
    └── NEWS_SENTIMENT_AGGREGATOR.md  # This file
```

## Recommended Workflow

### Daily Pre-Market Routine (9:00 AM ET)

1. **Run sentiment analysis** (before market open at 9:30 AM)
   ```bash
   python3 -m src.utils.news_sentiment --tickers "SPY,QQQ,NVDA,GOOGL"
   ```

2. **Review sentiment report**
   - Check which tickers have strong bullish/bearish signals
   - Note confidence levels
   - Compare with previous day's sentiment

3. **Integrate with trading strategy**
   - Use sentiment as confirmation signal
   - Combine with momentum indicators (MACD, RSI)
   - Let RL agent make final decision

4. **Save report**
   - Reports automatically saved to `data/sentiment/`
   - Track sentiment trends over time
   - Backtest correlation with price movements

### API Usage Budget (Free Tier)

With 25 Alpha Vantage calls/day:
- **Recommended**: Analyze 10-15 core tickers once per day
- **Core holdings**: SPY, QQQ, VOO (3 calls)
- **Growth stocks**: NVDA, GOOGL, AMZN, AAPL, MSFT (5 calls)
- **Watchlist**: 7-12 additional tickers
- **Reserve**: 5 calls for ad-hoc analysis

## Troubleshooting

### "No Alpha Vantage API key found"
**Solution**: Add `ALPHA_VANTAGE_API_KEY` to `.env` file

### "403 Forbidden" from Stocktwits
**Solution**: Rate limited (200/hour). Wait 10-15 minutes or reduce frequency

### "Expecting value: line 1 column 1" from Yahoo
**Solution**: Yahoo API changed. Script has fallback logic, but may need manual fix

### "rate_limit" error from Alpha Vantage
**Solution**: 25 calls/day exceeded. Wait until next day or upgrade to premium ($50/mo)

## Future Enhancements

### Phase 1 (Month 2)
- [ ] Add Reddit sentiment (r/wallstreetbets, r/stocks)
- [ ] Implement caching to avoid duplicate API calls
- [ ] Add historical sentiment tracking

### Phase 2 (Month 3-4)
- [ ] Integrate with CoreStrategy pre-market analysis
- [ ] Add sentiment-based position sizing
- [ ] Backtest sentiment correlation with returns

### Phase 3 (Month 5+)
- [ ] Add SEC EDGAR filings analysis
- [ ] Implement sentiment trend detection
- [ ] Add alert system for sentiment shifts

## Cost Analysis

| Service | Free Tier | Paid Tier | Recommended |
|---------|-----------|-----------|-------------|
| Yahoo Finance | Unlimited | N/A | Free |
| Stocktwits | 200/hour | N/A | Free |
| Alpha Vantage | 25/day | 75/day ($50/mo) | Start with Free |

**Total Cost**: $0/month (free tier sufficient for daily pre-market analysis)

**When to Upgrade**:
- If analyzing 25+ tickers daily
- If need intraday sentiment updates
- If making $100+/day profit (cost becomes negligible)

## Contact

Created by: Claude (CTO)
Project: AI Trading System
Date: November 9, 2025

For questions or issues, refer to `.claude/CLAUDE.md`
