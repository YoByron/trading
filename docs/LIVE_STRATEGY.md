# SPY Iron Condor - Live Strategy Specification

**Version**: 2.0.0 (Enhanced)  
**Date**: 2026-03-25  
**Canonical Source**: `src/strategies/core_strategy.py`

## 1. Strategy Overview
High-probability income generation via SPY Iron Condors, leveraging rapid theta decay and volatility mean reversion.

## 2. Entry Logic
- **Ticker**: SPY (Liquid ETF only)
- **Target DTE**: 30-45 Days (Standard) | 4 Days (Tactical)
- **Short Strikes**: 15-delta (True delta from live option chain)
- **Wing Width**: Dynamic by Volatility Regime:
    - VIX < 15: $5 wide
    - VIX 15-25: $10 wide
    - VIX > 25: $15 wide
- **Position Sizing**: 5% of Portfolio max per position.

## 3. Volatility Gate (Regime Aware)
- **VIX Bands**: OK to trade if $12 < \text{VIX} < 35$.
- **Edge Requirement**: $\text{IV} - \text{RV}_{20\text{d}} \ge 5\%$.
- **Signal**: VIX Mean Reversion (Enter on drop from spike).

## 4. Exit Logic (Canonical)
- **Profit Target**: 50% of Credit Received.
- **Stop Loss**: 100% of Credit Received (1x loss).
- **Time Exit**: 7 Days to Expiration (Gamma risk avoidance).

## 5. Safety & Observability
- **RAG Safety Guard**: Consults historical 'Lessons Learned' database for regime-specific failure patterns before entry.
- **Structured Journaling**: Every trade snapshots VIX, IV, RV, and RAG warnings for post-trade analysis.
- **Execution Gate**: Mandatory mid-price verification and bid/ask spread checks.
- **Step 8: Autonomous Promotion**: Successes and entries are broadcasted to X, LinkedIn, and Reddit via Zernio API.

## 6. Maintenance
- **Review Period**: Weekly RAG ingestion of closed trade PnL.
- **Circuit Breaker**: 2% Max Daily Drawdown.
