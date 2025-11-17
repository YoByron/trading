# CoinSnacks Newsletter Analyzer - Integration Guide

## Overview

The Newsletter Analyzer module provides autonomous consumption of CoinSnacks crypto trading signals. It uses a hybrid approach:

1. **Primary**: Read MCP-populated JSON files (Claude Desktop fetches, writes signals)
2. **Fallback**: Direct RSS parsing from CoinSnacks Medium feed

## Features

- Extract BTC/ETH trading signals from newsletter articles
- Parse technical analysis (entry, target, stop-loss, sentiment)
- Confidence scoring based on keyword analysis
- Timeframe detection (short/medium/long-term)
- Automatic signal persistence and retrieval

## File Locations

```
src/utils/newsletter_analyzer.py          # Main module
scripts/test_newsletter_analyzer.py       # Test suite
data/newsletter_signals/                  # Signal storage directory
data/newsletter_signals/EXAMPLE_FORMAT.json  # JSON format reference
```

## Quick Start

### 1. Install Dependencies

```bash
pip install feedparser==6.0.10
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Basic Usage

```python
from src.utils.newsletter_analyzer import get_btc_signal, get_eth_signal

# Get latest BTC signal (within last 7 days)
btc_signal = get_btc_signal(max_age_days=7)

if btc_signal:
    print(f"BTC: {btc_signal.sentiment} ({btc_signal.confidence:.2f} confidence)")
    if btc_signal.entry_price:
        print(f"Entry: ${btc_signal.entry_price:,.0f}")
    if btc_signal.target_price:
        print(f"Target: ${btc_signal.target_price:,.0f}")

# Get latest ETH signal
eth_signal = get_eth_signal(max_age_days=7)
```

### 3. Advanced Usage

```python
from src.utils.newsletter_analyzer import NewsletterAnalyzer

analyzer = NewsletterAnalyzer()

# Get all signals (BTC + ETH)
signals = analyzer.get_latest_signals(max_age_days=7)

for ticker, signal in signals.items():
    print(f"{ticker}: {signal.sentiment} ({signal.confidence:.2f})")

# Parse custom article text
article_text = """
BTC breaking above $46k with strong volume.
Entry: $46,500, Target: $50k, Stop: $44k
"""
parsed_signals = analyzer.parse_article(article_text)

# Save signals for later retrieval
analyzer.save_signals(parsed_signals)
```

## Signal Structure

```python
@dataclass
class CryptoSignal:
    ticker: str              # "BTC" or "ETH"
    sentiment: str           # "bullish", "bearish", "neutral"
    confidence: float        # 0.0 - 1.0
    entry_price: float       # Optional entry point
    target_price: float      # Optional profit target
    stop_loss: float         # Optional stop loss
    timeframe: str           # "short-term", "medium-term", "long-term"
    reasoning: str           # Excerpt explaining the signal
    source_date: datetime    # When signal was generated
```

## MCP Integration (Preferred Method)

### Step 1: Fetch CoinSnacks in Claude Desktop

Use MCP RSS tool to fetch latest CoinSnacks articles:

```
Hey Claude, fetch the latest CoinSnacks newsletter from:
https://medium.com/feed/coinsnacks

Extract BTC and ETH trading signals including:
- Bullish/bearish sentiment
- Entry prices
- Target prices
- Stop losses
- Reasoning
```

### Step 2: Save Signals to JSON

Claude Desktop writes signals to:
```
data/newsletter_signals/newsletter_signals_2025-11-17.json
```

Format (see `data/newsletter_signals/EXAMPLE_FORMAT.json`):

```json
{
  "BTC": {
    "ticker": "BTC",
    "sentiment": "bullish",
    "confidence": 0.85,
    "entry_price": 45500,
    "target_price": 52000,
    "stop_loss": 43000,
    "timeframe": "medium-term",
    "reasoning": "BTC showing strong momentum...",
    "source_date": "2025-11-17T00:00:00+00:00"
  },
  "ETH": {
    "ticker": "ETH",
    "sentiment": "bearish",
    "confidence": 0.65,
    "entry_price": null,
    "target_price": 2100,
    "stop_loss": null,
    "timeframe": "short-term",
    "reasoning": "ETH facing resistance...",
    "source_date": "2025-11-17T00:00:00+00:00"
  }
}
```

### Step 3: Trading Script Reads Signals

```python
# In your trading script (e.g., autonomous_trader.py)
from src.utils.newsletter_analyzer import get_btc_signal, get_eth_signal

btc_signal = get_btc_signal()
eth_signal = get_eth_signal()

# Use signals in trading decisions
if btc_signal and btc_signal.sentiment == "bullish" and btc_signal.confidence > 0.7:
    # Consider BTC long position
    execute_trade("BTC", "buy", btc_signal.entry_price)
```

## RSS Fallback (Automatic)

If no MCP-populated files exist, the module automatically falls back to parsing RSS feed:

```python
analyzer = NewsletterAnalyzer()

# This will try MCP files first, then RSS if needed
signals = analyzer.get_latest_signals()
```

**Note**: RSS fallback requires `feedparser` library to be installed.

## Sentiment Analysis

The analyzer uses keyword-based sentiment scoring:

### Bullish Keywords
- bullish, buy, long, breakout, rally, uptrend
- accumulate, support, bottom, undervalued, pump
- moon, calls, strong, momentum, reversal up

### Bearish Keywords
- bearish, sell, short, breakdown, dump, downtrend
- distribute, resistance, top, overvalued, crash
- puts, weak, consolidation, reversal down

### Technical Indicators (Boost Confidence)
- RSI, MACD, moving average, MA, EMA, SMA
- Volume, Fibonacci, golden cross, death cross
- Bollinger bands, support/resistance, trendlines

### Confidence Calculation

```python
confidence = 0.5 + (keyword_count * 0.1) + (technical_indicators * 0.05)
# Capped at 1.0
```

Example:
- 3 bullish keywords + 2 technical indicators = 0.5 + 0.3 + 0.1 = 0.9 confidence

## Testing

Run the test suite to verify functionality:

```bash
python3 scripts/test_newsletter_analyzer.py
```

Tests cover:
1. Article parsing (sample CoinSnacks content)
2. MCP file reading
3. Convenience functions (get_btc_signal, get_eth_signal)
4. Signal persistence (save/load)

## Integration with Trading System

### Example: Daily Trading Workflow

```python
# In autonomous_trader.py or daily_execution.py

from src.utils.newsletter_analyzer import get_btc_signal, get_eth_signal
from datetime import datetime

def should_trade_crypto(ticker: str) -> bool:
    """Check if newsletter signals support trading this crypto"""

    signal = get_btc_signal() if ticker == "BTC" else get_eth_signal()

    if not signal:
        logger.info(f"No newsletter signal for {ticker}")
        return False

    # Check signal age (only trade on recent signals)
    signal_age_days = (datetime.now() - signal.source_date).days
    if signal_age_days > 7:
        logger.info(f"{ticker} signal too old ({signal_age_days} days)")
        return False

    # Check confidence threshold
    if signal.confidence < 0.6:
        logger.info(f"{ticker} confidence too low ({signal.confidence:.2f})")
        return False

    # Check sentiment alignment with strategy
    if signal.sentiment != "bullish":
        logger.info(f"{ticker} not bullish (sentiment: {signal.sentiment})")
        return False

    logger.info(f"{ticker} signal: {signal.sentiment} ({signal.confidence:.2f} confidence)")
    return True

def get_entry_price(ticker: str) -> float:
    """Get suggested entry price from newsletter"""
    signal = get_btc_signal() if ticker == "BTC" else get_eth_signal()
    return signal.entry_price if signal and signal.entry_price else None

def get_target_price(ticker: str) -> float:
    """Get profit target from newsletter"""
    signal = get_btc_signal() if ticker == "BTC" else get_eth_signal()
    return signal.target_price if signal and signal.target_price else None
```

### Example: Risk Management Integration

```python
from src.core.risk_manager import RiskManager
from src.utils.newsletter_analyzer import get_btc_signal

risk_manager = RiskManager(...)
btc_signal = get_btc_signal()

if btc_signal and btc_signal.stop_loss:
    # Use newsletter stop-loss in risk calculation
    risk_per_share = abs(current_price - btc_signal.stop_loss)
    position_size = risk_manager.calculate_position_size(
        ticker="BTC",
        entry_price=current_price,
        stop_loss=btc_signal.stop_loss
    )
```

## Limitations

1. **Keyword-based**: Simple sentiment analysis, not LLM-powered
2. **Price Extraction**: Regex-based, may miss complex formats
3. **No Context Understanding**: Doesn't understand nuanced market analysis
4. **Manual MCP Population**: Requires Claude Desktop to populate JSON files

## Future Enhancements

- [ ] LLM-powered sentiment analysis (OpenRouter integration)
- [ ] Multi-source aggregation (CoinSnacks + other newsletters)
- [ ] Historical signal performance tracking
- [ ] Signal quality scoring (backtest against actual outcomes)
- [ ] Automatic MCP scheduling (weekly newsletter fetch)

## Troubleshooting

### No signals returned

```python
signals = get_btc_signal()
# Returns None
```

**Solutions**:
1. Check if MCP files exist: `ls data/newsletter_signals/`
2. Verify file format matches `EXAMPLE_FORMAT.json`
3. Check signal age (default: last 7 days only)
4. Install feedparser for RSS fallback: `pip install feedparser`

### Price extraction failing

If prices aren't being extracted:
1. Ensure prices are formatted as: `$45,000` or `$45k`
2. Check for context keywords near prices (entry, target, stop loss)
3. Test with sample article in test suite

### Low confidence scores

Confidence below 0.5 indicates:
- Few bullish/bearish keywords detected
- No technical indicators mentioned
- Neutral or mixed sentiment article

## Support

For issues or enhancements:
1. Run test suite: `python3 scripts/test_newsletter_analyzer.py`
2. Check logs for detailed error messages
3. Review example format: `data/newsletter_signals/EXAMPLE_FORMAT.json`
4. Verify feedparser installation: `python3 -c "import feedparser; print(feedparser.__version__)"`

## License

Part of the autonomous trading system. See project root LICENSE.
