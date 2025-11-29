# Holiday Crypto Trading

**Status**: ✅ **IMPLEMENTED**
**Date**: November 26, 2025

## Overview

The trading system now automatically executes crypto trades on market holidays when stock markets are closed. This leverages the 24/7 nature of cryptocurrency markets to maintain trading activity even when traditional markets are closed.

## How It Works

### Detection Logic

The system detects market holidays by:
1. Checking if it's a weekday (Monday-Friday)
2. Checking Alpaca's market clock API to see if markets are closed
3. If both conditions are true → **Holiday detected** → Switch to crypto mode

### Execution Flow

```
Weekday + Market Closed = Holiday → Crypto Mode
Weekend (Sat/Sun) = Crypto Mode
Weekday + Market Open = Stock Trading Mode
```

### Code Implementation

**Location**: `scripts/autonomous_trader.py`

**Key Function**:
```python
def is_market_holiday():
    """
    Check if today is a market holiday (market closed on a weekday).

    Uses Alpaca's clock API to determine if market is closed.
    If market is closed AND it's a weekday, it's a holiday.
    """
    clock = api.get_clock()
    is_weekday = datetime.now().weekday() < 5
    return is_weekday and not clock.is_open
```

**Mode Detection**:
```python
is_holiday = is_market_holiday()
is_weekend_day = is_weekend()
crypto_mode = args.crypto_only or is_weekend_day or is_holiday
```

## Supported Holidays

The system automatically handles all US market holidays, including:
- **New Year's Day** (January 1)
- **Martin Luther King Jr. Day** (Third Monday in January)
- **Presidents Day** (Third Monday in February)
- **Good Friday** (Friday before Easter)
- **Memorial Day** (Last Monday in May)
- **Juneteenth** (June 19)
- **Independence Day** (July 4)
- **Labor Day** (First Monday in September)
- **Thanksgiving** (Fourth Thursday in November)
- **Christmas** (December 25)

## Benefits

1. **24/7 Trading**: Crypto markets never close, so we can trade on holidays
2. **No Manual Intervention**: System automatically detects holidays
3. **Consistent Execution**: Same crypto strategy on weekends and holidays
4. **Capital Efficiency**: No missed trading days due to market closures

## Configuration

**Daily Crypto Investment**: $0.50/day (configurable via `CRYPTO_DAILY_AMOUNT`)

**Strategy**: Same crypto strategy as weekends:
- BTC/USD and ETH/USD analysis
- Momentum-based selection (MACD, RSI, Volume)
- Graham-Buffett safety checks
- 7% stop-loss (crypto volatility)

## Example: Thanksgiving 2025

**Date**: November 27, 2025 (Thursday)

**What Happens**:
1. GitHub Actions workflow runs at 9:35 AM ET (weekday schedule)
2. Script detects: Weekday + Market Closed = Holiday
3. Switches to crypto mode automatically
4. Executes crypto strategy (BTC/ETH analysis)
5. Places crypto trade if conditions are met

**Result**: Crypto trade executes on Thanksgiving instead of skipping the day

## Testing

To test holiday crypto trading manually:

```bash
# Force crypto mode (simulates holiday)
python3 scripts/autonomous_trader.py --crypto-only

# Check if market is closed (on actual holiday)
python3 -c "
from scripts.autonomous_trader import is_market_holiday
print('Is holiday:', is_market_holiday())
"
```

## Related Files

- `scripts/autonomous_trader.py` - Main trading script with holiday detection
- `.github/workflows/daily-trading.yml` - Runs on weekdays (includes holidays)
- `src/strategies/crypto_strategy.py` - Crypto trading strategy
- `docs/CRYPTO_SAFETY_INTEGRATION.md` - Crypto safety checks

## Future Enhancements

Potential improvements:
- [ ] Add explicit holiday calendar for better visibility
- [ ] Track holiday crypto performance separately
- [ ] Adjust crypto allocation on holidays (currently same as weekends)
- [ ] Add holiday-specific crypto strategies
