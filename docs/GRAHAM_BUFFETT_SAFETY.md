# Graham-Buffett Investment Safety Module

## Overview

This module implements the core investment principles of **Benjamin Graham** and **Warren Buffett** to keep investments safe. It provides comprehensive safety analysis before executing trades, ensuring we only invest in quality companies at attractive prices.

## Core Principles Implemented

### 1. Margin of Safety (Benjamin Graham)

**Principle**: Only buy when the market price is significantly below the intrinsic value.

**Implementation**:
- Calculates intrinsic value using DCF (Discounted Cash Flow) analysis
- Requires minimum **20% discount** to intrinsic value (configurable)
- Ideal margin of safety: **30% discount** (Graham's preference)
- Rejects trades when trading at premium to intrinsic value

**Example**:
```
Intrinsic Value: $100
Market Price: $70
Margin of Safety: 30% ✅ (Excellent - proceed)
```

### 2. Quality Companies (Warren Buffett)

**Principle**: Invest only in high-quality businesses with strong fundamentals.

**Implementation**:
- **Debt-to-Equity Ratio**: Maximum 50% (lower is better)
- **Current Ratio**: Minimum 1.0 (liquidity check)
- **Return on Equity (ROE)**: Minimum 10% (efficiency)
- **Return on Assets (ROA)**: Minimum 5% (asset efficiency)
- **Profit Margin**: Minimum 10% (profitability)
- **Earnings Growth**: Minimum 5% annual growth
- **Earnings Consistency**: Tracks consistency of earnings over time

**Quality Score**: Composite 0-100 score based on all metrics

### 3. Circle of Competence (Warren Buffett)

**Principle**: Invest only in businesses you understand.

**Implementation**:
- Focuses on well-known, established companies
- Minimum market cap: **$1 billion** (large-cap companies)
- Pre-approved list of well-known tickers (AAPL, MSFT, GOOGL, etc.)
- ETFs are always acceptable (SPY, QQQ, VOO, etc.)

### 4. Long-Term Perspective

**Principle**: Think long-term, avoid frequent trading.

**Implementation**:
- Reduces trading frequency by rejecting low-quality opportunities
- Focuses on holding quality positions
- Avoids speculative trades

### 5. Emotional Discipline

**Principle**: Be fearful when others are greedy, greedy when others are fearful.

**Implementation**:
- Rejects trades when no margin of safety exists
- Avoids buying at peaks (already handled by momentum filters)
- Waits for pullbacks and attractive valuations

### 6. Diversification

**Principle**: Proper position sizing and diversification.

**Implementation**:
- Integrated with existing risk management system
- Position size limits (max 50% per symbol)
- Diversification across asset classes

## Usage

### Basic Usage

```python
from src.safety.graham_buffett_safety import get_global_safety_analyzer

# Get safety analyzer
safety_analyzer = get_global_safety_analyzer()

# Analyze a stock
analysis = safety_analyzer.analyze_safety(
    symbol="AAPL",
    market_price=150.00
)

# Check if should buy
should_buy, analysis = safety_analyzer.should_buy(
    symbol="AAPL",
    market_price=150.00
)

if should_buy:
    print(f"✅ {analysis.symbol} approved - Rating: {analysis.safety_rating.value}")
    print(f"   Margin of Safety: {analysis.margin_of_safety_pct*100:.1f}%")
    print(f"   Quality Score: {analysis.quality.quality_score:.1f}/100")
else:
    print(f"❌ {analysis.symbol} rejected - Rating: {analysis.safety_rating.value}")
    for reason in analysis.reasons:
        print(f"   Reason: {reason}")
```

### Integration with Trading Strategy

The safety module is automatically integrated into the core trading strategy. It runs before every trade execution.

**Enable/Disable**:
```bash
# Enable (default)
USE_GRAHAM_BUFFETT_SAFETY=true

# Disable
USE_GRAHAM_BUFFETT_SAFETY=false
```

### Custom Configuration

```python
from src.safety.graham_buffett_safety import GrahamBuffettSafety

# Custom configuration
safety_analyzer = GrahamBuffettSafety(
    min_margin_of_safety=0.25,  # Require 25% discount
    require_quality_screening=True,
    require_circle_of_competence=True,
)
```

## Safety Ratings

The module assigns one of five safety ratings:

1. **EXCELLENT**: High margin of safety (≥30%) + high quality (≥70/100)
2. **GOOD**: Adequate margin of safety (≥20%) + good quality (≥60/100)
3. **ACCEPTABLE**: Either good margin OR good quality (but not both)
4. **POOR**: Low margin of safety AND low quality
5. **REJECT**: No margin of safety (premium) OR very low quality (<30/100)

**Trading Behavior**:
- **EXCELLENT, GOOD, ACCEPTABLE**: Trade proceeds
- **POOR, REJECT**: Trade is blocked

## Example Output

```
✅ AAPL PASSED Graham-Buffett Safety Check (Rating: excellent)
   Margin of Safety: 35.2%
   Quality Score: 82.5/100
   Reasons:
   - Excellent margin of safety: 35.2% (ideal: 30.0%)
   - High quality company (score: 82.5/100)
```

```
❌ TSLA REJECTED by Graham-Buffett Safety Module
   Safety Rating: reject
   Reasons:
   - No margin of safety - trading at premium: 15.3% above intrinsic value
   - Low quality company (score: 28.3/100) - fails quality screening
   Warnings:
   - ⚠️  Trading at premium to intrinsic value - no margin of safety
   - ⚠️  Low quality company - fails fundamental screening criteria
```

## Configuration Parameters

### Margin of Safety Thresholds

```python
MIN_MARGIN_OF_SAFETY = 0.20  # 20% minimum discount required
IDEAL_MARGIN_OF_SAFETY = 0.30  # 30% ideal discount (Graham's preference)
```

### Quality Thresholds

```python
MAX_DEBT_TO_EQUITY = 0.50  # Maximum 50% debt-to-equity ratio
MIN_CURRENT_RATIO = 1.0  # Minimum current ratio (liquidity)
MIN_ROE = 0.10  # Minimum 10% return on equity
MIN_ROA = 0.05  # Minimum 5% return on assets
MIN_PROFIT_MARGIN = 0.10  # Minimum 10% net profit margin
MIN_EARNINGS_GROWTH = 0.05  # Minimum 5% annual earnings growth
```

### Circle of Competence

```python
MIN_MARKET_CAP = 1_000_000_000  # $1B minimum market cap
ESTABLISHED_COMPANIES_ONLY = True  # Only invest in established companies
```

## Data Sources

- **Intrinsic Value**: DCF calculation using Polygon.io or Alpha Vantage
- **Company Fundamentals**: Yahoo Finance (yfinance)
- **Market Data**: Real-time prices from Alpaca API

## Limitations

1. **DCF Calculation**: Requires free cash flow data, which may not be available for all companies
2. **Data Quality**: Relies on third-party data sources (Yahoo Finance, Polygon.io, Alpha Vantage)
3. **ETFs**: ETFs are always approved (no fundamental analysis for ETFs)
4. **Market Cap Check**: For unknown tickers, checks market cap to determine if in circle of competence

## Best Practices

1. **Enable for All Trades**: Keep `USE_GRAHAM_BUFFETT_SAFETY=true` to protect capital
2. **Review Rejections**: Check why trades were rejected to understand market conditions
3. **Adjust Thresholds**: For more conservative approach, increase `min_margin_of_safety` to 0.30
4. **Monitor Quality Scores**: Track quality scores over time to identify deteriorating companies

## References

- **Benjamin Graham**: "The Intelligent Investor" - Margin of Safety concept
- **Warren Buffett**: Berkshire Hathaway shareholder letters - Quality investing
- **Value Investing**: Focus on intrinsic value vs. market price

## Integration Points

The safety module integrates with:

1. **Core Strategy** (`src/strategies/core_strategy.py`): Runs before trade execution
2. **DCF Valuation** (`src/utils/dcf_valuation.py`): Calculates intrinsic value
3. **Risk Manager** (`src/core/risk_manager.py`): Works alongside existing risk controls

## Intelligent Investor Enhancements (2025-11-24)

### New Features Added

1. **Defensive Investor Score (0-100)**
   - Evaluates stocks against Graham's defensive investor criteria
   - Considers P/E ratio (<15 preferred, <20 maximum)
   - Considers P/B ratio (<1.5 preferred, <2.0 maximum)
   - Considers dividend yield (>2% preferred)
   - Considers debt-to-equity and liquidity

2. **Mr. Market Sentiment Assessment**
   - Implements Graham's "Mr. Market" concept
   - Identifies when market is "fearful" (buying opportunity)
   - Identifies when market is "greedy" (be cautious)
   - Uses intrinsic value discount and P/E ratios as proxies

3. **Value Score (0-100)**
   - Composite score combining margin of safety, quality, and defensive criteria
   - Helps prioritize the best value opportunities
   - Weighted: 40% margin of safety, 30% quality, 30% defensive score

4. **Enhanced Safety Rating**
   - Now considers defensive investor score in rating determination
   - Rejects stocks with P/E > 20 or P/B > 2.0 (strict limits)
   - More conservative approach aligned with Graham's principles

5. **Integration with Trading Strategies**
   - CoreStrategy (Tier 1 - ETFs): Safety check before every trade
   - GrowthStrategy (Tier 2 - Stocks): Safety check before every trade
   - Can be enabled/disabled via `use_intelligent_investor` parameter

6. **Enhanced Diversification Rules**
   - Maximum 30% per position (Graham recommended 25% for defensive investor)
   - Minimum 2-3 positions for proper diversification
   - Prevents over-concentration in single positions

### Usage Example

```python
from src.safety.graham_buffett_safety import get_global_safety_analyzer

safety_analyzer = get_global_safety_analyzer()

# Analyze a stock with Intelligent Investor principles
analysis = safety_analyzer.analyze_safety("AAPL", market_price=150.00)

print(f"Safety Rating: {analysis.safety_rating.value}")
print(f"Margin of Safety: {analysis.margin_of_safety_pct*100:.1f}%")
print(f"Defensive Investor Score: {analysis.defensive_investor_score:.1f}/100")
print(f"Mr. Market Sentiment: {analysis.mr_market_sentiment}")
print(f"Value Score: {analysis.value_score:.1f}/100")

if analysis.quality:
    print(f"P/E Ratio: {analysis.quality.pe_ratio:.1f}")
    print(f"P/B Ratio: {analysis.quality.pb_ratio:.2f}")
    print(f"Dividend Yield: {analysis.quality.dividend_yield*100:.2f}%")
```

### Configuration

The Intelligent Investor principles are enabled by default. To disable:

```python
# In CoreStrategy
strategy = CoreStrategy(use_intelligent_investor=False)

# In GrowthStrategy
strategy = GrowthStrategy(use_intelligent_investor=False)
```

### Key Principles Implemented

1. **Margin of Safety**: Minimum 20% discount to intrinsic value
2. **Defensive Investor Criteria**: P/E < 15, P/B < 1.5, dividend yield > 2%
3. **Mr. Market Concept**: Buy when fearful, avoid when greedy
4. **Value Investing**: Focus on intrinsic value vs market price
5. **Diversification**: Max 30% per position, minimum 2-3 positions
6. **Quality Screening**: Strong fundamentals, low debt, consistent earnings

## Future Enhancements

- [ ] Add competitive advantage analysis (moat detection)
- [ ] Implement Graham's Net Current Asset Value (NCAV) screening
- [ ] Add management quality scoring
- [ ] Industry-specific quality thresholds
- [ ] Historical quality trend analysis
- [ ] Defensive vs Enterprising investor mode selection

---

**Remember**: This module is designed to **protect capital** by ensuring we only invest in quality companies at attractive prices. It may reduce trading frequency, but that's by design - quality over quantity, following Benjamin Graham's timeless principles from "The Intelligent Investor".
