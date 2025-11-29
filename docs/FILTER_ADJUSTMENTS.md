# Crypto Trading Filter Adjustments

## Current Filters (Too Conservative)

### Hard Filter 1: MACD Histogram
- **Current**: Must be > 0 (strictly bullish)
- **Problem**: Too restrictive - misses opportunities when MACD is recovering
- **Impact**: Both BTC and ETH rejected this weekend (-627.96 and -10.57)

### Hard Filter 2: RSI
- **Current**: Must be < 60 (not overbought)
- **Status**: ✅ Reasonable

### Hard Filter 3: Volume
- **Current**: Must be > 1.0 (above average)
- **Status**: ✅ Reasonable

## Proposed Adjustments

### Option 1: Relax MACD Filter (RECOMMENDED)
Change from `macd_histogram > 0` to `macd_histogram > -50`

**Rationale**:
- Allows trades when MACD is recovering from bearish
- Still filters out strongly bearish conditions
- More opportunities while maintaining risk control

**Implementation**:
```python
# OLD (too strict):
if macd_histogram < 0:
    reject

# NEW (configurable):
macd_threshold = float(os.getenv("CRYPTO_MACD_THRESHOLD", "-50.0"))
if macd_histogram < macd_threshold:
    reject
```

### Option 2: Make MACD a Soft Filter
Instead of hard rejection, reduce score for bearish MACD:
- MACD > 0: +10 points
- MACD > -50: +5 points
- MACD < -50: reject

### Option 3: Use MACD Trend Instead of Absolute Value
Check if MACD is improving (trending up) rather than requiring it to be positive:
- If MACD histogram improved over last 3 days: allow trade
- If MACD histogram declining: reject

## Environment Variable Control

Add `CRYPTO_MACD_THRESHOLD` environment variable:
- Default: `-50.0` (less conservative)
- Set to `0` for original strict behavior
- Set to `-100` for very permissive

## Testing

After adjustment, test with:
```bash
python3 scripts/autonomous_trader.py --crypto-only
```

Check if trades now execute when MACD is slightly negative but improving.

---

**Status**: ✅ **IMPLEMENTED** - MACD threshold now configurable via `CRYPTO_MACD_THRESHOLD`
**Default**: `-50.0` (less conservative than original `0`)
**Date**: November 24, 2025
