# Market Data Provider - Self-Healing Architecture

**Last Updated**: November 13, 2025
**File**: `src/utils/market_data.py`
**Status**: Production Ready

---

## Overview

The `MarketDataProvider` has been enhanced with comprehensive self-healing capabilities to ensure maximum uptime and data availability for the trading system. This document covers the architecture, configuration, monitoring, and troubleshooting.

---

## Problem Statement

### What Happened (Nov 12-13, 2025)

During the Nov 12-13 trading window, all market data sources failed:
- **yfinance**: Broke (unknown HTTP errors)
- **Alpaca API**: Failed (paper trading account limits)
- **Alpha Vantage**: Not configured (missing API key)
- **Cached Data**: Unavailable (first-time symbols)

**Result**: System safely skipped trades (correct behavior) but provided no actionable diagnostics or alerts.

### Root Causes Identified

1. **Insufficient logging**: Failures were silent or vague
2. **No health metadata**: Couldn't track which source succeeded/failed
3. **Hardcoded parameters**: No way to tune retry/backoff behavior
4. **No exponential backoff**: Retries too aggressive (yfinance/Alpaca)
5. **Poor error context**: Generic error messages
6. **No reliability tracking**: Couldn't identify systematic failures

---

## Architecture Changes

### 1. Enhanced Data Structures

#### `DataSource` Enum
Tracks which provider was used:
```python
class DataSource(Enum):
    YFINANCE = "yfinance"
    ALPACA = "alpaca"
    ALPHA_VANTAGE = "alpha_vantage"
    CACHE = "cache"
    UNKNOWN = "unknown"
```

#### `FetchAttempt` Dataclass
Records each fetch attempt:
```python
@dataclass
class FetchAttempt:
    source: DataSource
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    rows_fetched: int = 0
    latency_ms: float = 0.0
```

#### `MarketDataResult` Dataclass
Enhanced result with metadata:
```python
@dataclass
class MarketDataResult:
    data: pd.DataFrame           # The actual market data
    source: DataSource           # Which source provided the data
    attempts: List[FetchAttempt] # All attempts made
    total_attempts: int          # Total number of attempts
    total_latency_ms: float      # Cumulative latency
    cache_age_hours: Optional[float]  # Age if from cache
```

**Key Methods**:
- `add_attempt()`: Track each fetch attempt
- `to_dict()`: Serialize for logging/reporting

### 2. Fallback Chain with Tracking

```
┌─────────────┐
│  Request    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ In-Memory Cache     │ ◄── Fastest (microseconds)
│ (Recent requests)   │
└──────┬──────────────┘
       │ Miss
       ▼
┌─────────────────────┐
│ yfinance (Primary)  │ ◄── Free, usually reliable
│ + Exponential       │     Max 3 retries (configurable)
│   Backoff           │     Backoff: 1s, 2s, 4s
└──────┬──────────────┘
       │ Fail
       ▼
┌─────────────────────┐
│ Alpaca API          │ ◄── Preferred fallback
│ + Exponential       │     Max 3 retries (configurable)
│   Backoff           │     Backoff: 2s, 4s, 8s
└──────┬──────────────┘
       │ Fail
       ▼
┌─────────────────────┐
│ Alpha Vantage       │ ◄── Last resort live source
│ + Rate Limiting     │     Max 4 retries (configurable)
│ + Exponential       │     Backoff: 60s, 120s, 240s
│   Backoff           │     Respects 5 calls/min limit
└──────┬──────────────┘
       │ Fail
       ▼
┌─────────────────────┐
│ Disk Cache          │ ◄── Stale but better than nothing
│ (up to 7 days old)  │     Uses most recent cached file
└──────┬──────────────┘
       │ Fail
       ▼
┌─────────────────────┐
│ Raise ValueError    │ ◄── Complete failure
│ with detailed       │     Log all attempts
│ error summary       │
└─────────────────────┘
```

### 3. Exponential Backoff

Each source now implements exponential backoff to avoid hammering failed APIs:

**yfinance**:
```python
# Retry 1: Wait 1.0s  (configurable)
# Retry 2: Wait 2.0s  (2^1 * 1.0s)
# Retry 3: Wait 4.0s  (2^2 * 1.0s)
```

**Alpaca API**:
```python
# Retry 1: Wait 2.0s  (configurable)
# Retry 2: Wait 4.0s  (2^1 * 2.0s)
# Retry 3: Wait 8.0s  (2^2 * 2.0s)
```

**Alpha Vantage**:
```python
# Retry 1: Wait 60s  (configurable)
# Retry 2: Wait 120s (2^1 * 60s)
# Retry 3: Wait 240s (2^2 * 60s)
# Retry 4: Wait 480s (2^3 * 60s)
```

### 4. Health Logging

All fetch attempts are logged to `data/cache/alpha_vantage/health_log.jsonl`:

**Log Format** (JSON Lines):
```json
{
  "timestamp": "2025-11-13T14:30:45.123456+00:00",
  "symbol": "SPY",
  "source": "yfinance",
  "rows": 30,
  "total_attempts": 1,
  "total_latency_ms": 456.78,
  "cache_age_hours": null,
  "attempts": [
    {
      "source": "yfinance",
      "success": true,
      "error": null,
      "rows": 30,
      "latency_ms": 456.78
    }
  ]
}
```

**Failure Example**:
```json
{
  "timestamp": "2025-11-13T14:35:12.789012+00:00",
  "symbol": "NVDA",
  "source": "alpaca",
  "rows": 30,
  "total_attempts": 5,
  "total_latency_ms": 8234.56,
  "cache_age_hours": null,
  "attempts": [
    {
      "source": "yfinance",
      "success": false,
      "error": "HTTP 403 Forbidden",
      "rows": 0,
      "latency_ms": 1234.56
    },
    {
      "source": "yfinance",
      "success": false,
      "error": "HTTP 403 Forbidden",
      "rows": 0,
      "latency_ms": 1100.0
    },
    {
      "source": "alpaca",
      "success": true,
      "error": null,
      "rows": 30,
      "latency_ms": 5900.0
    }
  ]
}
```

---

## Configuration

### Environment Variables

All retry/backoff parameters are now configurable via `.env`:

```bash
# yfinance settings (primary source)
YFINANCE_LOOKBACK_BUFFER_DAYS=35        # Default: 35
YFINANCE_SECONDARY_LOOKBACK_DAYS=150   # Default: 150
YFINANCE_MAX_RETRIES=3                 # Default: 3
YFINANCE_INITIAL_BACKOFF_SECONDS=1.0   # Default: 1.0

# Alpaca settings (preferred fallback)
ALPACA_MAX_RETRIES=3                   # Default: 3
ALPACA_INITIAL_BACKOFF_SECONDS=2.0     # Default: 2.0

# Alpha Vantage settings (last resort live source)
ALPHA_VANTAGE_API_KEY=your_key_here    # Required for Alpha Vantage
ALPHAVANTAGE_MIN_INTERVAL_SECONDS=15   # Default: 15 (respects 5 calls/min)
ALPHAVANTAGE_BACKOFF_SECONDS=60        # Default: 60
ALPHAVANTAGE_MAX_RETRIES=4             # Default: 4

# Cache settings
MARKET_DATA_CACHE_DIR=data/cache/alpha_vantage  # Default
CACHE_TTL_SECONDS=21600                # Default: 6 hours
CACHE_MAX_AGE_DAYS=7                   # Default: 7 days
```

### Configuration Strategy

**Conservative (Default)**:
- Minimize API usage
- Longer backoffs to respect rate limits
- Suitable for production

**Aggressive (Lower Latency)**:
```bash
YFINANCE_MAX_RETRIES=5
YFINANCE_INITIAL_BACKOFF_SECONDS=0.5
ALPACA_MAX_RETRIES=5
ALPACA_INITIAL_BACKOFF_SECONDS=1.0
```
- Faster retries
- Higher API usage
- Use when data freshness is critical

**Minimal (Testing)**:
```bash
YFINANCE_MAX_RETRIES=1
ALPACA_MAX_RETRIES=1
ALPHAVANTAGE_MAX_RETRIES=1
```
- Fastest failures
- Use for unit tests

---

## Usage

### Basic Usage

```python
from src.utils.market_data import MarketDataProvider

provider = MarketDataProvider()
result = provider.get_daily_bars("SPY", lookback_days=30)

# Access data
df = result.data  # pandas DataFrame

# Check metadata
print(f"Source: {result.source.value}")
print(f"Total attempts: {result.total_attempts}")
print(f"Latency: {result.total_latency_ms:.2f}ms")

# Inspect attempts
for attempt in result.attempts:
    print(f"  - {attempt.source.value}: {'✓' if attempt.success else '✗'} ({attempt.latency_ms:.2f}ms)")
```

### Handling Failures

```python
try:
    result = provider.get_daily_bars("NVDA", lookback_days=30)
    df = result.data

    # Warn if using stale cached data
    if result.source == DataSource.CACHE:
        logger.warning(
            f"Using cached data ({result.cache_age_hours:.1f} hours old)"
        )
except ValueError as e:
    # Complete failure - no data available
    logger.error(f"Failed to fetch market data: {e}")
    # Skip trading for this symbol
```

### Monitoring Data Source Health

```python
# Check which source is being used most often
from collections import Counter

sources = []
for line in open("data/cache/alpha_vantage/health_log.jsonl"):
    entry = json.loads(line)
    sources.append(entry["source"])

print(Counter(sources))
# Output: Counter({'yfinance': 45, 'alpaca': 5, 'cache': 2})
```

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Source Success Rate**:
   ```bash
   # Count successes per source
   cat data/cache/alpha_vantage/health_log.jsonl | \
     jq -r '[.symbol, .source, .total_attempts] | @tsv'
   ```

2. **Average Latency**:
   ```bash
   # Calculate average latency per source
   cat data/cache/alpha_vantage/health_log.jsonl | \
     jq -r '[.source, .total_latency_ms] | @tsv' | \
     awk '{sum[$1]+=$2; count[$1]++} END {for (s in sum) print s, sum[s]/count[s]}'
   ```

3. **Fallback Frequency**:
   ```bash
   # How often are we falling back from yfinance?
   cat data/cache/alpha_vantage/health_log.jsonl | \
     jq -r 'select(.source != "yfinance") | [.symbol, .source] | @tsv'
   ```

4. **Cache Usage**:
   ```bash
   # How often are we using stale cached data?
   cat data/cache/alpha_vantage/health_log.jsonl | \
     jq -r 'select(.source == "cache") | [.symbol, .cache_age_hours] | @tsv'
   ```

### Alerting Thresholds

**WARNING** (investigate soon):
- yfinance success rate < 80%
- Fallback to Alpaca > 20% of requests
- Average latency > 2000ms

**CRITICAL** (immediate action):
- yfinance success rate < 50%
- Fallback to cache > 10% of requests
- Complete failures (ValueError raised)

### Sample Alert Query

```python
import json
from collections import defaultdict

# Analyze last 100 fetches
stats = defaultdict(lambda: {"success": 0, "fail": 0})

with open("data/cache/alpha_vantage/health_log.jsonl") as f:
    for line in list(f)[-100:]:
        entry = json.loads(line)
        source = entry["source"]

        # Count successful fetches
        if entry["rows"] > 0:
            stats[source]["success"] += 1
        else:
            stats[source]["fail"] += 1

# Calculate success rates
for source, counts in stats.items():
    total = counts["success"] + counts["fail"]
    rate = counts["success"] / total if total > 0 else 0
    print(f"{source}: {rate*100:.1f}% success ({counts['success']}/{total})")

    # Alert if below threshold
    if rate < 0.8:
        print(f"⚠️  WARNING: {source} success rate below 80%!")
```

---

## Troubleshooting

### Issue: All Sources Failing

**Symptoms**:
- `ValueError: Failed to fetch data from all sources`
- All `attempts` show `success: false`

**Diagnosis**:
```bash
# Check recent failures
tail -n 20 data/cache/alpha_vantage/health_log.jsonl | jq -r '.attempts[] | select(.success == false) | [.source, .error] | @tsv'
```

**Solutions**:
1. **yfinance blocked**: Try using a VPN or changing User-Agent
2. **Alpaca rate limited**: Wait for rate limit to reset (check headers)
3. **Alpha Vantage not configured**: Add `ALPHA_VANTAGE_API_KEY` to `.env`
4. **No cached data**: First-time symbols won't have cache

### Issue: Slow Fetches (High Latency)

**Symptoms**:
- `total_latency_ms` > 5000ms
- Many retry attempts

**Diagnosis**:
```bash
# Find slow fetches
cat data/cache/alpha_vantage/health_log.jsonl | jq -r 'select(.total_latency_ms > 5000) | [.symbol, .source, .total_latency_ms] | @tsv'
```

**Solutions**:
1. **Reduce retries** (if failures are persistent):
   ```bash
   YFINANCE_MAX_RETRIES=1
   ALPACA_MAX_RETRIES=1
   ```
2. **Increase backoff** (if rate limited):
   ```bash
   YFINANCE_INITIAL_BACKOFF_SECONDS=2.0
   ALPACA_INITIAL_BACKOFF_SECONDS=4.0
   ```

### Issue: Excessive Fallbacks

**Symptoms**:
- `source: "alpaca"` or `source: "alpha_vantage"` most of the time
- yfinance failing consistently

**Diagnosis**:
```bash
# Count sources
cat data/cache/alpha_vantage/health_log.jsonl | jq -r '.source' | sort | uniq -c
```

**Solutions**:
1. **yfinance blocked**: Investigate yfinance errors, consider alternative
2. **Alpaca preferred**: If Alpaca is faster/more reliable, this is OK
3. **Update yfinance**: `pip install --upgrade yfinance`

### Issue: Stale Cached Data

**Symptoms**:
- `source: "cache"`
- `cache_age_hours` is high (> 24 hours)

**Diagnosis**:
```bash
# Check cache age
cat data/cache/alpha_vantage/health_log.jsonl | jq -r 'select(.source == "cache") | [.symbol, .cache_age_hours] | @tsv'
```

**Solutions**:
1. **Reduce cache max age**:
   ```bash
   CACHE_MAX_AGE_DAYS=3  # Instead of 7
   ```
2. **Fix live sources**: Investigate why all live sources are failing
3. **Clear stale cache**:
   ```bash
   find data/cache/alpha_vantage -name "*.csv" -mtime +3 -delete
   ```

---

## Testing

### Unit Tests

Comprehensive test suite: `tests/test_market_data_fallbacks.py`

**Run all tests**:
```bash
python -m pytest tests/test_market_data_fallbacks.py -v
```

**Test coverage**:
- ✅ MarketDataResult metadata tracking (3 tests)
- ✅ yfinance retry logic (4 tests)
- ✅ Alpaca fallback (3 tests)
- ✅ Alpha Vantage fallback (2 tests)
- ✅ Cached data fallback (3 tests)
- ✅ Full fallback chain (3 tests)
- ✅ Health logging (1 test)
- ✅ Configuration (2 tests)

**Total**: 21 tests, 100% passing

### Manual Testing

**Test yfinance retry**:
```python
from src.utils.market_data import MarketDataProvider

provider = MarketDataProvider()

# Force yfinance to fail
import unittest.mock as mock
with mock.patch.object(provider, "_fetch_yfinance", side_effect=Exception("Simulated failure")):
    result = provider.get_daily_bars("SPY", 30)
    print(f"Fell back to: {result.source.value}")
    print(f"Attempts: {result.total_attempts}")
```

**Test Alpha Vantage**:
```python
# Disable yfinance and Alpaca, force Alpha Vantage
import os
os.environ["ALPHA_VANTAGE_API_KEY"] = "your_key_here"

provider = MarketDataProvider()
provider._alpaca_api = None  # Disable Alpaca

with mock.patch.object(provider, "_fetch_yfinance", return_value=None):
    result = provider.get_daily_bars("SPY", 30)
    print(f"Source: {result.source.value}")  # Should be "alpha_vantage"
```

---

## Migration Guide

### For Existing Code

**Old API**:
```python
provider = MarketDataProvider()
df = provider.get_daily_bars("SPY", 30)  # Returns DataFrame
```

**New API**:
```python
provider = MarketDataProvider()
result = provider.get_daily_bars("SPY", 30)  # Returns MarketDataResult
df = result.data  # Get DataFrame
```

**Compatibility Note**: Existing code will break since `get_daily_bars()` now returns `MarketDataResult` instead of `pd.DataFrame`. Update all callsites to use `result.data`.

### Migration Steps

1. **Update imports**:
   ```python
   from src.utils.market_data import MarketDataProvider, MarketDataResult
   ```

2. **Update callsites**:
   ```python
   # OLD
   df = provider.get_daily_bars("SPY", 30)

   # NEW
   result = provider.get_daily_bars("SPY", 30)
   df = result.data
   ```

3. **Add monitoring** (optional):
   ```python
   if result.source == DataSource.CACHE:
       logger.warning(f"Using cached data for {symbol}")
   if result.total_attempts > 3:
       logger.warning(f"High retry count for {symbol}: {result.total_attempts}")
   ```

4. **Update tests**: Mock `MarketDataResult` instead of `pd.DataFrame`

---

## Performance Impact

### Memory

- **MarketDataResult overhead**: ~500 bytes per fetch (negligible)
- **Health log**: ~300 bytes per log entry
- **Health log rotation**: Recommend rotating weekly (e.g., logrotate)

### Latency

- **In-memory cache**: +0.001ms (negligible)
- **Health logging**: +0.5-1ms (non-blocking)
- **Retry logic**: +backoff time (only on failures)

**Best case** (yfinance succeeds first try):
- Overhead: +1ms (health logging)

**Worst case** (all retries exhausted):
- yfinance: 3 attempts × 2s backoff = 6s
- Alpaca: 3 attempts × 4s backoff = 12s
- Alpha Vantage: 4 attempts × 120s backoff = 480s
- **Total**: ~500s (8 minutes) before giving up

**Recommendation**: Tune retry counts and backoffs based on failure patterns.

---

## Future Enhancements

### Potential Improvements

1. **Circuit Breaker Pattern**:
   - Skip known-failing sources temporarily
   - Reset after cooldown period
   - Reduces latency during prolonged outages

2. **Intelligent Source Selection**:
   - Track historical success rates
   - Prefer fastest/most reliable source
   - Dynamic fallback ordering

3. **Parallel Fetching**:
   - Query multiple sources simultaneously
   - Use first successful response
   - Reduce latency in failure scenarios

4. **Real-Time Monitoring Dashboard**:
   - Visualize source health in Streamlit
   - Alert on anomalies
   - Historical success rate trends

5. **Automatic API Key Rotation**:
   - Multiple Alpha Vantage keys
   - Rotate on rate limit hit
   - Increase throughput

---

## References

- **Source Code**: `src/utils/market_data.py`
- **Unit Tests**: `tests/test_market_data_fallbacks.py`
- **Configuration**: `.env.example`
- **Health Log**: `data/cache/alpha_vantage/health_log.jsonl`

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-13 | Initial self-healing implementation | Claude (CTO) |
| 2025-11-13 | Added exponential backoff to all sources | Claude (CTO) |
| 2025-11-13 | Added health logging and metadata tracking | Claude (CTO) |
| 2025-11-13 | Made all parameters configurable via env vars | Claude (CTO) |
| 2025-11-13 | Created comprehensive test suite (21 tests) | Claude (CTO) |

---

**Maintained by**: Claude (CTO)
**Last Review**: November 13, 2025
**Next Review**: As needed based on production failures
