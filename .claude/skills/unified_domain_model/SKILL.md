# Unified Domain Model Skill

## Purpose

Ensure consistency across all trading system components using Netflix's "Upper Metamodel" pattern.

## When to Use

- Creating new trades, signals, or positions
- Converting data between formats (Alpaca, yfinance, JSON)
- Adding new domain concepts to the system
- Ensuring type safety in trading operations

## Core Classes

```python
from src.core.unified_domain_model import (
    # Enums
    AssetClass, TradeAction, OrderStatus, SignalStrength, StrategyTier,
    # Domain Objects
    Symbol, Price, Signal, Trade, Position, Portfolio,
    # Factory
    factory
)
```

## Quick Examples

### Create a Crypto Trade
```python
from src.core.unified_domain_model import factory, TradeAction, StrategyTier, Price, Trade

# Create symbol
btc = factory.create_crypto_symbol("BTCUSD")

# Create trade
trade = Trade(
    id="trade_001",
    symbol=btc,
    action=TradeAction.BUY,
    quantity=0.00011,
    price=Price(value=90125.56),
    notional=25.0,
    strategy=StrategyTier.TIER5_CRYPTO
)

# Project to different formats
alpaca_order = trade.to_alpaca_order()  # For broker
json_data = trade.to_dict()              # For storage
```

### Create a Trading Signal
```python
signal = factory.create_signal(
    symbol=btc,
    action=TradeAction.BUY,
    confidence=0.85,
    source="text_analyzer"
)

if signal.is_actionable(min_confidence=0.6):
    execute_trade(signal)
```

### Symbol Format Conversion
```python
symbol = factory.create_crypto_symbol("BTCUSD")
print(symbol.to_alpaca())    # "BTCUSD"
print(symbol.to_yfinance())  # "BTC-USD"
```

## Available Enums

| Enum | Values |
|------|--------|
| `AssetClass` | equity, crypto, option, etf, bond |
| `TradeAction` | BUY, SELL, HOLD |
| `OrderStatus` | pending, submitted, filled, partial, cancelled, rejected |
| `SignalStrength` | strong_buy, buy, hold, sell, strong_sell |
| `StrategyTier` | tier1_safe, tier2_momentum, tier3_swing, tier4_options, tier5_crypto |

## Integration Points

The unified domain model integrates with:
- `crypto_strategy.py` - Use `Trade` and `Signal` objects
- `autonomous_trader.py` - Use `factory.create_trade_from_alpaca()`
- `system_state.json` - Use `Portfolio.to_dict()`
- `trades_*.json` - Use `Trade.to_dict()`

## Source

Based on Netflix's Upper Metamodel: "Model Once, Represent Everywhere"
