# CoinSnacks Newsletter Workflow

## Overview

Claude Code (CTO) autonomously fetches CoinSnacks newsletter every Sunday, analyzes crypto market signals, and populates structured JSON for Python trading scripts to consume.

## Workflow Timeline

### Sunday Morning Workflow

**8:00 AM ET** - Newsletter Fetch & Analysis (Claude Code)
1. Claude Code receives scheduled reminder (via launchd or manual trigger)
2. Uses MCP RSS tool to fetch latest CoinSnacks article from https://coinsnacks.com/feed/
3. Analyzes article content for:
   - BTC sentiment (bullish/bearish/neutral)
   - ETH sentiment (bullish/bearish/neutral)
   - Recommended coin (BTC/ETH/NONE)
   - Key reasoning and insights
   - Confidence score (0.0-1.0)
4. Writes structured signals to `data/newsletter_signals_YYYY-MM-DD.json`
5. Reports to CEO via Telegram: "CoinSnacks signals fetched: [BTC: bullish, ETH: neutral, Recommended: BTC]"

**10:00 AM ET** - Crypto Trading Execution (Python Script)
1. `crypto_strategy.py` executes on schedule
2. Reads `data/newsletter_signals_YYYY-MM-DD.json`
3. Compares CoinSnacks signals to our momentum indicators (MACD + RSI + Volume)
4. Makes combined decision:
   - If signals agree → Higher confidence trade
   - If signals conflict → Lower position size or skip
   - If newsletter unavailable → Fall back to momentum-only
5. Executes BTC/ETH trades via Alpaca
6. Logs decision reasoning in trade metadata

## MCP Tool Usage (Claude Code)

### Fetching CoinSnacks

**Tool**: MCP RSS Reader (or Web Fetch if RSS unavailable)

**Steps**:
```
1. Fetch: https://coinsnacks.com/feed/
2. Parse: Latest article (usually Sunday morning publication)
3. Extract: Full article content
4. Analyze: Use Claude's NLP to identify:
   - Sentiment indicators (bullish/bearish language)
   - Price predictions or recommendations
   - Risk warnings
   - Technical analysis mentions
5. Synthesize: Convert to structured JSON signals
```

**Example MCP Call**:
```python
# Claude Code will use MCP tool like this:
newsletter_content = mcp.fetch_rss("https://coinsnacks.com/feed/", limit=1)
signals = claude_analyze(newsletter_content)
write_json(signals, f"data/newsletter_signals_{date}.json")
```

## Signal Format

### Output JSON Structure

**File**: `data/newsletter_signals_YYYY-MM-DD.json`

**Required Fields**:
```json
{
  "date": "2025-11-17",
  "source": "CoinSnacks",
  "btc_signal": "bullish",
  "eth_signal": "neutral",
  "recommended_coin": "BTC",
  "reasoning": "CoinSnacks highlights institutional BTC buying and ETF inflows. ETH mentioned as consolidating with no clear direction.",
  "confidence": 0.85,
  "fetched_at": "2025-11-17 08:15:32"
}
```

**Optional Fields** (for enhanced analysis):
```json
{
  "newsletter_url": "https://coinsnacks.com/weekly-crypto-market-analysis",
  "status": "fetched",
  "key_insights": [
    "Institutional BTC accumulation continues",
    "ETH gas fees declining",
    "Altcoin season signals weak"
  ],
  "signal_strength": {
    "btc": 0.8,
    "eth": 0.5
  },
  "comparison_notes": "Our momentum agrees on BTC bullish, conflicts on ETH (we see bearish)"
}
```

## Python Integration

### Reading Signals in crypto_strategy.py

```python
import json
from datetime import datetime
from pathlib import Path

def load_newsletter_signals():
    """Load today's CoinSnacks signals if available."""
    today = datetime.now().strftime("%Y-%m-%d")
    signal_file = Path(f"data/newsletter_signals_{today}.json")

    if not signal_file.exists():
        return None  # Fall back to momentum-only

    with open(signal_file, 'r') as f:
        signals = json.load(f)

    # Validate signals are fresh (not stale template)
    if signals.get("status") == "pending_fetch":
        return None

    return signals

def combine_signals(momentum_signal, newsletter_signal):
    """Combine our momentum signals with CoinSnacks analysis."""
    if newsletter_signal is None:
        return momentum_signal, 1.0  # Full confidence in our system

    # Agreement → High confidence
    if momentum_signal == newsletter_signal["btc_signal"]:
        return momentum_signal, 1.0

    # Conflict → Lower confidence or skip
    if momentum_signal == "bullish" and newsletter_signal["btc_signal"] == "bearish":
        return "neutral", 0.3  # Reduce position or skip

    # Newsletter stronger → Blend signals
    return newsletter_signal["btc_signal"], newsletter_signal["confidence"]
```

## Scheduling

### Option 1: Manual Trigger (Current)

**Every Sunday morning**:
1. CEO reminds Claude Code: "Fetch CoinSnacks signals"
2. Claude Code executes fetch workflow
3. Signals ready by 10:00 AM for crypto trades

### Option 2: Automated (Future)

**Using launchd (macOS)**:
```xml
<!-- ~/Library/LaunchAgents/com.trading.newsletter.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.newsletter</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/osascript</string>
        <string>-e</string>
        <string>display notification "Time to fetch CoinSnacks signals" with title "Trading System"</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer> <!-- Sunday -->
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

**Note**: This just creates a reminder. Claude Code still executes the actual fetch.

## Error Handling

### Scenario 1: Newsletter Not Published Yet

**Problem**: CoinSnacks hasn't published Sunday article yet at 8:00 AM

**Solution**:
1. Claude Code creates template with `status: "pending_fetch"`
2. Python script detects pending status → Falls back to momentum-only
3. Claude Code retries at 9:00 AM if CEO requests

### Scenario 2: MCP Tool Unavailable

**Problem**: MCP RSS tool fails or is unavailable

**Solution**:
1. Claude Code attempts manual web fetch using WebFetch tool
2. If all tools fail → Create template with `status: "fetch_failed"`
3. Python script falls back to momentum-only (our system is primary)
4. Log warning to CEO report: "CoinSnacks unavailable, trading on momentum only"

### Scenario 3: Signal Unclear

**Problem**: Newsletter doesn't clearly indicate BTC/ETH signals

**Solution**:
1. Claude Code uses best judgment based on:
   - Overall sentiment (bullish/bearish language)
   - Price predictions mentioned
   - Risk warnings vs. opportunity highlights
2. Sets lower confidence score (0.3-0.5)
3. Adds reasoning: "Signal inferred from general sentiment, not explicit recommendation"

## Signal Priority

**Decision Hierarchy** (in crypto_strategy.py):

1. **Circuit Breakers** (highest priority)
   - Max drawdown limits
   - Daily loss limits
   - Consecutive loss limits

2. **Our Momentum Signals** (primary)
   - MACD + RSI + Volume analysis
   - 60-day backtested system
   - Proven win rate >60%

3. **CoinSnacks Signals** (validation layer)
   - Confirms or challenges our momentum
   - Adjusts confidence/position size
   - Adds fundamental context

**Remember**: CoinSnacks is a SANITY CHECK, not the primary signal. Our momentum system drives decisions.

## Success Criteria

**Newsletter integration is successful if**:
- ✅ Signals fetched 90%+ of Sundays
- ✅ JSON format consistent and parseable
- ✅ Combined decisions improve win rate by 5-10%
- ✅ CEO receives fetch confirmations via Telegram
- ✅ System gracefully falls back when newsletter unavailable

**Newsletter integration should be removed if**:
- ❌ Win rate decreases vs. momentum-only
- ❌ Fetch reliability <50%
- ❌ Signals consistently conflict with profitable momentum trades

## Claude Code Responsibilities

**Every Sunday (Manual or Automated)**:
1. ✅ Fetch CoinSnacks at 8:00 AM
2. ✅ Analyze and extract signals
3. ✅ Write structured JSON to data/
4. ✅ Report to CEO: "Signals ready for 10:00 AM crypto trades"
5. ✅ Include in daily report: "CoinSnacks alignment: [agreed/conflicted]"

**Monthly Review**:
1. ✅ Analyze: Did CoinSnacks signals improve or hurt performance?
2. ✅ Report: Win rate with vs. without newsletter
3. ✅ Recommend: Keep, adjust weight, or remove

## CEO Expectations

**What CEO Should See**:
- Sunday morning Telegram: "CoinSnacks fetched: BTC bullish, ETH neutral"
- Daily report: "CoinSnacks agreed with our momentum → High confidence trade"
- Monthly report: "Newsletter integration added +3% to win rate"

**What CEO Should NOT Have To Do**:
- ❌ Manually fetch newsletters
- ❌ Parse newsletter content
- ❌ Convert to JSON
- ❌ Remember to fetch weekly

**CTO owns this end-to-end.**

## Future Enhancements

**Phase 2 (Month 4+)**:
- [ ] Add multiple newsletter sources (Bankless, The Defiant)
- [ ] Sentiment aggregation across 3-5 sources
- [ ] Historical newsletter signal tracking
- [ ] Win rate by newsletter source (which sources add value?)

**Phase 3 (Month 6+)**:
- [ ] NLP-based signal extraction (no manual analysis)
- [ ] Automated RSS monitoring (check hourly for new articles)
- [ ] Multi-timeframe analysis (weekly vs. daily signals)

## References

- **CoinSnacks Website**: https://coinsnacks.com/
- **RSS Feed**: https://coinsnacks.com/feed/
- **MCP Documentation**: Claude Code uses built-in MCP tools
- **Related**: `crypto_strategy.py` (signal consumer)
- **Related**: `.claude/CLAUDE.md` (CTO responsibilities)

---

**Created**: November 17, 2025
**Owner**: Claude Code (CTO)
**Reviewed**: CEO (Igor Ganapolsky)
