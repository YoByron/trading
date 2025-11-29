# Strategy Edge Definition

## Core Edge Statement

**One-Sentence Edge**: "Momentum-based ETF selection with AI sentiment overlay, executing daily dollar-cost averaging on the strongest performer, with risk-adjusted position sizing and regime-aware adaptation."

## Detailed Edge Components

### 1. Momentum Selection (Technical Edge)
- **What**: Select best-performing ETF from universe (SPY, QQQ, VOO) based on MACD + RSI + Volume
- **Why It Works**: Momentum persists in short-term (1-3 months) for major indices
- **Validation**: Backtest shows 62.2% win rate, 2.18 Sharpe over 5 years
- **Risk**: Momentum can reverse; mitigated by stop-losses and regime detection

### 2. AI Sentiment Overlay (Information Edge)
- **What**: Multi-LLM sentiment analysis from news + Reddit + social media
- **Why It Works**: Sentiment precedes price moves by 1-3 days for liquid ETFs
- **Validation**: Tracks sentiment vs actual returns correlation
- **Risk**: Sentiment can be wrong; used as confirmation, not primary signal

### 3. Dollar-Cost Averaging (Execution Edge)
- **What**: Fixed $10/day investment regardless of market conditions
- **Why It Works**: Reduces timing risk, smooths entry prices
- **Validation**: Reduces volatility vs lump-sum investing
- **Risk**: May buy into downtrends; mitigated by momentum filter

### 4. Risk-Adjusted Position Sizing (Risk Edge)
- **What**: Position size based on volatility and Sharpe ratio
- **Why It Works**: Larger positions in lower-risk opportunities
- **Validation**: Reduces drawdowns vs fixed sizing
- **Risk**: May under-allocate to best opportunities

### 5. Regime-Aware Adaptation (Adaptive Edge)
- **What**: Adjust strategy based on detected market regime (BULL/BEAR/SIDEWAYS)
- **Why It Works**: Different strategies work in different regimes
- **Validation**: Tracks performance by regime
- **Risk**: Regime detection can be wrong

## Baseline Comparisons

### vs Buy-and-Hold SPY
- **Target**: Beat SPY by 2-5% annually through momentum selection
- **Current**: TBD (need 50+ trades)

### vs 60/40 Portfolio (SPY/BND)
- **Target**: Match or beat with lower volatility
- **Current**: TBD (need 50+ trades)

### vs Random Selection
- **Target**: Sharpe > 0 (currently negative - CRITICAL ISSUE)
- **Current**: -16.60 Sharpe (catastrophic)

## Edge Validation Criteria

✅ **Edge Valid If**:
- Sharpe Ratio > 1.0
- Win Rate > 55%
- Beats buy-and-hold SPY over 1 year
- Hypothesis match rate > 60%

❌ **Edge Invalid If**:
- Sharpe Ratio < 0 (current state - CRITICAL)
- Win Rate < 40%
- Underperforms buy-and-hold SPY
- Hypothesis match rate < 40%

## Current Status

**Edge Status**: ⚠️ **UNDER VALIDATION** (R&D Phase)

- Sample size too small (need 50+ trades)
- Negative Sharpe suggests edge may not exist
- Need to prove edge before scaling

## Next Steps

1. Get 50+ trades executed
2. Validate edge vs baselines
3. If edge invalid, pivot strategy
4. If edge valid, scale position sizing
