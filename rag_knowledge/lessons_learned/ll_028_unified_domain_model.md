# LL-028: Netflix Upper Metamodel - Unified Domain Model

**Date**: 2025-12-13
**Severity**: HIGH
**Category**: Architecture
**Impact**: System-wide consistency, reduced bugs, easier integration

## Executive Summary

Implemented Netflix's "Upper Metamodel" pattern for our trading system. Single source of truth for all domain concepts (Trade, Signal, Position, Portfolio) that generates consistent representations across all systems.

## The Problem (Spider-Man Problem)

Before: Each component had its own definition of core concepts:
- `crypto_strategy.py` had one Trade format
- `autonomous_trader.py` had another
- `system_state.json` had a third
- `trades_*.json` had yet another

This caused:
- Inconsistent data across systems
- Bugs from format mismatches
- Difficult integrations
- Code duplication

## The Solution (Model Once, Represent Everywhere)

Created `src/core/unified_domain_model.py` with:

### Core Domain Objects
- `Symbol` - Unified symbol representation (projects to Alpaca, yfinance formats)
- `Signal` - Trading signals with confidence and strength
- `Trade` - Core trade object with projections to all formats
- `Position` - Portfolio positions
- `Portfolio` - Account state

### Key Pattern
```python
# Define once
trade = Trade(
    symbol=Symbol("BTCUSD", AssetClass.CRYPTO),
    action=TradeAction.BUY,
    notional=25.0,
    strategy=StrategyTier.TIER5_CRYPTO
)

# Project everywhere
alpaca_order = trade.to_alpaca_order()     # Broker format
json_record = trade.to_dict()               # Storage format
perf_record = trade.to_performance_record() # Analytics format
```

## Benefits

1. **Consistency** - Single definition for all concepts
2. **Discoverability** - Standard enums for all valid values
3. **Interoperability** - Easy conversion between formats
4. **Validation** - Type-safe domain objects
5. **Automation** - Generate schemas from models

## Source

Netflix Engineering Blog: "Model Once, Represent Everywhere: UDA (Unified Data Architecture)"
- https://blog.thewitslab.com/model-once-represent-everywhere
- https://www.infoq.com/news/2025/12/netflix-upper-uda-architecture

## Files

- Implementation: `src/core/unified_domain_model.py`
- Skill: `.claude/skills/unified_domain_model/SKILL.md`

## Tags

#architecture #netflix #domain-model #consistency #upper-metamodel
