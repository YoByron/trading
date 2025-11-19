# 🔧 Troubleshooting Guide

**Last Updated**: November 19, 2025  
**Purpose**: Quick reference for common issues and recovery procedures

---

## 🚨 Quick Diagnosis

### Workflow Failed - Where to Look

1. **GitHub Actions Logs**: Actions tab → Failed run → Job logs
2. **Sentry** (if configured): Check for error notifications
3. **Performance Log**: `data/performance_log.json` - Last successful update
4. **System State**: `data/system_state.json` - Current system status

---

## Common Issues & Fixes

### 1. Workflow Cancelled (Timeout)

**Symptoms**:
- Workflow shows "Cancelled" status
- No trades executed
- Performance log not updated

**Root Causes**:
- Alpha Vantage exponential backoff (FIXED: Now 90s max timeout)
- Data source failures cascading (FIXED: Reliable sources first)
- Old code running (FIXED: Always checkout latest main)

**Fix**:
```bash
# Verify latest code is deployed
git log --oneline -1

# Manual recovery: Update performance log
python3 scripts/update_performance_log.py

# Next run will use latest code automatically
```

**Prevention**: ✅ Fixed in Nov 19, 2025 - Data source priority reordering

---

### 2. Data Source Failures

**Symptoms**:
- "yfinance returned insufficient data"
- "Alpaca API failed"
- "Alpha Vantage rate-limited"

**Diagnosis**:
```bash
# Check which data sources are configured
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Alpaca:', '✅' if os.getenv('ALPACA_API_KEY') else '❌')
print('Polygon:', '✅' if os.getenv('POLYGON_API_KEY') else '❌')
print('Alpha Vantage:', '✅' if os.getenv('ALPHA_VANTAGE_API_KEY') else '❌')
"
```

**Fix**:
- System automatically falls back through priority order:
  1. Alpaca API (most reliable)
  2. Polygon.io (reliable paid)
  3. Cached data (< 24 hours old)
  4. yfinance (unreliable free)
  5. Alpha Vantage (avoid if rate-limited)

**If All Fail**:
- System will skip trading day (better than bad data)
- Use cached data if available
- Check API status pages

---

### 3. Performance Log Not Updated

**Symptoms**:
- `data/performance_log.json` missing today's entry
- Last entry is from yesterday

**Causes**:
- Workflow cancelled before completion
- Script error before log update
- Manual execution didn't complete

**Fix**:
```bash
# Manual update
python3 scripts/update_performance_log.py

# Verify update
cat data/performance_log.json | jq '.[-1]'
```

---

### 4. API Authentication Errors

**Symptoms**:
- "401 Unauthorized"
- "Invalid API key"
- "Authentication failed"

**Fix**:
1. Verify GitHub Secrets are set:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `POLYGON_API_KEY` (optional but recommended)
   - `ALPHA_VANTAGE_API_KEY` (optional)

2. Check API keys are valid:
```bash
# Test Alpaca
python3 scripts/check_alpaca_status.py

# Test Polygon (if configured)
python3 -c "
from polygon import RESTClient
import os
from dotenv import load_dotenv
load_dotenv()
client = RESTClient(os.getenv('POLYGON_API_KEY'))
print('Polygon API:', '✅' if client else '❌')
"
```

---

### 5. Import Errors

**Symptoms**:
- "ModuleNotFoundError: No module named 'X'"
- "ImportError: cannot import name 'Y'"

**Fix**:
```bash
# Verify requirements.txt is up to date
pip install -r requirements.txt

# Check Python version (should be 3.11)
python3 --version
```

---

### 6. Order Execution Failures

**Symptoms**:
- Orders submitted but not filled
- "Insufficient buying power"
- "Invalid order parameters"

**Diagnosis**:
```bash
# Check account status
python3 scripts/check_alpaca_status.py

# Check recent orders
python3 -c "
import alpaca_trade_api as tradeapi
import os
from dotenv import load_dotenv
load_dotenv()
api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), 'https://paper-api.alpaca.markets')
orders = api.list_orders(status='all', limit=5)
for o in orders:
    print(f'{o.symbol}: {o.status} - {o.filled_qty}/{o.qty} @ ${o.filled_avg_price}')
"
```

**Fix**:
- Check account balance
- Verify order size is valid (> $1 minimum)
- Check market hours (9:30 AM - 4:00 PM ET)

---

## Manual Recovery Procedures

### When Workflow Fails Completely

**Step 1: Diagnose**
```bash
# Check GitHub Actions logs
gh run view --log

# Check system state
cat data/system_state.json | jq '.last_updated'
```

**Step 2: Update Performance Log**
```bash
python3 scripts/update_performance_log.py
```

**Step 3: Verify Next Run**
```bash
# Check workflow is scheduled
gh workflow view daily-trading.yml

# Verify latest code is deployed
git log --oneline -1
```

---

### Emergency Stop

**Stop All Trading**:
```bash
# Disable workflow
gh workflow disable .github/workflows/daily-trading.yml

# Trip circuit breaker
python3 -c "
from src.safety.circuit_breakers import CircuitBreaker
CircuitBreaker()._trip_breaker('MANUAL', 'Emergency stop')
"
```

**Resume Trading**:
```bash
# Re-enable workflow
gh workflow enable .github/workflows/daily-trading.yml

# Reset circuit breaker (if needed)
python3 -c "
from src.safety.circuit_breakers import CircuitBreaker
CircuitBreaker().manual_reset()
"
```

---

## Health Check Script

Run this to verify system health:

```bash
python3 scripts/health_check.py
```

**Checks**:
- ✅ API keys configured
- ✅ API connectivity
- ✅ Data freshness
- ✅ System state valid
- ✅ Performance log up to date

---

## Getting Help

1. **Check Logs**: `logs/trading_system.log`
2. **Check Sentry**: If configured, errors appear there
3. **Review Recent Changes**: `git log --oneline -10`
4. **Check Documentation**: `docs/` directory

---

## Prevention Checklist

Before each trading day, verify:

- [ ] Latest code is deployed (`git log -1`)
- [ ] API keys are valid (`scripts/check_alpaca_status.py`)
- [ ] Workflow is enabled (`gh workflow view daily-trading.yml`)
- [ ] Performance log updated yesterday (`cat data/performance_log.json | jq '.[-1]'`)
- [ ] No circuit breakers tripped (`cat data/system_state.json | jq '.circuit_breaker'`)

---

## Related Documentation

- `docs/PLAN.md` - Infrastructure reliability fixes
- `docs/CI_ARCHITECTURE.md` - Workflow details
- `.claude/skills/error_handling_protocols/SKILL.md` - Error handling protocols

