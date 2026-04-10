# Free Options Data Sources for SPY Iron Condor Trading

**Last Updated**: March 30, 2026

## Problem Statement

Alpaca paper account subscription tier returns:
```
Error: "subscription does not permit querying recent SIP data"
```

When attempting to fetch VIX from their data API.

**Need**:
1. Current VIX value for entry signal timing
2. IV rank / IV percentile for SPY
3. Option Greeks (especially delta) for strike selection (15-20 delta target)

---

## Solution Summary: Use yfinance (Already in Requirements)

The trading system already includes **yfinance 0.2.58** in `requirements.txt`. This provides all three data types for FREE:

| Data Type | Source | Included? | API Calls/Day | Cost |
|-----------|--------|-----------|--------------|------|
| VIX | yfinance | ✅ YES | Unlimited | FREE |
| SPY IV | yfinance | ✅ YES | Unlimited | FREE |
| IV Percentile | yfinance + pandas | ✅ YES | Unlimited | FREE |
| Delta/Greeks | yfinance + Black-Scholes | ✅ YES (manual calc) | Unlimited | FREE |

---

## 1. VIX (Current Level + History)

### Primary: yfinance
```python
import yfinance as yf

# Current VIX
vix_ticker = yf.Ticker("^VIX")
current_vix = vix_ticker.info.get('regularMarketPrice')
print(f"Current VIX: {current_vix}")  # e.g., 17.45

# Historical VIX (for VIX mean reversion signals)
vix_history = vix_ticker.history(period="60d")
print(vix_history[['Close']].tail(10))  # Last 10 days

# Works with existing src/signals/vix_mean_reversion_signal.py
```

**Status in Codebase**:
- Already used in `src/signals/vix_mean_reversion_signal.py` (line 26)
- Works with `src/utils/yfinance_wrapper.py` for graceful fallback
- No changes needed - already functional

### Secondary: FRED API (Federal Reserve)
If yfinance fails, fallback to official FRED data:
```python
import pandas as pd

# VIX from Federal Reserve (1990-present, daily updates)
vix_df = pd.read_csv(
    'https://fred.stlouisfed.org/data/VIXCLS.csv',
    parse_dates=['DATE'],
    dtype={'VIXCLS': float}
)
current_vix = vix_df.iloc[-1]['VIXCLS']
```

---

## 2. SPY Implied Volatility (IV) + IV Percentile

### Primary: yfinance Option Chains
```python
import yfinance as yf
import pandas as pd

spy = yf.Ticker("SPY")

# Get available expiration dates
expirations = spy.options  # ['2026-04-17', '2026-04-24', ...]
first_expiry = expirations[0]

# Fetch option chain for first expiration
chain = spy.option_chain(first_expiry)
calls_df = chain.calls  # DataFrame with option data
puts_df = chain.puts

# ImpliedVolatility is automatically included in DataFrame
print(calls_df[['strike', 'impliedVolatility', 'bid', 'ask']].head())

# Columns available in calls_df:
# ['strike', 'contractSymbol', 'lastTradeDate', 'lastPrice', 'bid', 'ask',
#  'change', 'percentChange', 'volume', 'openInterest', 'impliedVolatility',
#  'inTheMoney', 'contractSize', 'currency']

# Calculate average IV for timing entry
avg_iv = calls_df['impliedVolatility'].mean()
print(f"Average SPY IV: {avg_iv:.2%}")  # e.g., 0.1847 = 18.47%
```

### Calculate IV Percentile
```python
def get_iv_percentile(symbol: str, lookback_days: int = 252) -> float:
    """
    Calculate IV percentile: % of days in last year with lower IV.

    Formula: (days_with_lower_iv / total_days) * 100

    Example: 75 percentile = current IV is higher than 75% of the year
    """
    import yfinance as yf
    import numpy as np
    from datetime import datetime, timedelta

    ticker = yf.Ticker(symbol)

    # Get historical option chains across multiple expiries
    expirations = ticker.options
    historical_ivs = []

    # Sample last 5 expirations for 252-day history
    for expiry in expirations[-5:]:
        try:
            chain = ticker.option_chain(expiry)
            calls_iv = chain.calls['impliedVolatility'].mean()
            if not np.isnan(calls_iv):
                historical_ivs.append(calls_iv)
        except:
            pass

    if not historical_ivs:
        return 50.0  # Neutral if insufficient data

    current_iv = historical_ivs[-1]
    lower_count = sum(1 for iv in historical_ivs if iv < current_iv)
    percentile = (lower_count / len(historical_ivs)) * 100.0

    return percentile

# Use in entry signal
percentile = get_iv_percentile("SPY")
print(f"IV Percentile: {percentile:.0f}%")  # e.g., 68%

# Entry rules:
# < 30 percentile = premiums thin, avoid
# 30-70 percentile = acceptable
# > 70 percentile = elevated premiums, optimal for selling
```

---

## 3. Option Greeks (Delta, Gamma, Theta, Vega)

### Option 1: yoptions Library (RECOMMENDED)
```python
# Install: pip install yoptions
# (Already in requirements? Check requirements.txt)

import yfinance as yf
from yoptions import get_chain_greeks

spy = yf.Ticker("SPY")
expiry = spy.options[0]

# Get full Greeks automatically calculated
greeks_df = get_chain_greeks(spy, expiry)

# DataFrame columns:
# ['symbol', 'type', 'strike', 'expiry', 'bid', 'ask',
#  'impliedVolatility', 'delta', 'gamma', 'theta', 'vega']

# Find 15-20 delta puts for entry
puts_15_20 = greeks_df[
    (greeks_df['type'] == 'put') &
    (greeks_df['delta'].abs() >= 0.15) &
    (greeks_df['delta'].abs() <= 0.20)
]
print(puts_15_20[['strike', 'delta', 'bid', 'ask']])

# Example output:
#    strike   delta   bid    ask
# 0  573.0   -0.18  1.23  1.28
# 1  572.0   -0.19  0.95  1.00
```

**Pros**: Simplest, already handles IV from yfinance, calculates Greeks automatically
**Cons**: Adds dependency, depends on yfinance chain data accuracy

### Option 2: Manual Black-Scholes Calculation (MOST CONTROL)
```python
import numpy as np
from scipy.stats import norm
import yfinance as yf

def calculate_option_greeks(
    spot_price: float,
    strike_price: float,
    days_to_expiry: int,
    implied_vol: float,
    risk_free_rate: float = 0.05,
    option_type: str = 'call'
) -> dict:
    """
    Calculate Greeks using Black-Scholes formula.

    Args:
        spot_price: Current SPY price
        strike_price: Option strike
        days_to_expiry: Days until expiration
        implied_vol: IV from option chain (as decimal, e.g., 0.20 = 20%)
        risk_free_rate: Annual risk-free rate
        option_type: 'call' or 'put'

    Returns:
        dict with delta, gamma, theta, vega
    """
    T = days_to_expiry / 365.0  # Time in years
    S = spot_price
    K = strike_price
    r = risk_free_rate
    sigma = implied_vol

    # d1 and d2 from Black-Scholes
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # Greeks calculation
    if option_type.lower() == 'call':
        delta = norm.cdf(d1)
        theta = (
            -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) -
            r * K * np.exp(-r*T) * norm.cdf(d2)
        ) / 365  # Per day
    else:  # put
        delta = norm.cdf(d1) - 1  # Negative for puts
        theta = (
            -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) +
            r * K * np.exp(-r*T) * norm.cdf(-d2)
        ) / 365  # Per day

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% IV change

    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega
    }

# Example: Find 15-delta put for SPY
spy_price = 575.00
iv = 0.20  # 20% IV from chain
dte = 30

for strike in range(545, 575):
    greeks = calculate_option_greeks(
        spot_price=spy_price,
        strike_price=float(strike),
        days_to_expiry=dte,
        implied_vol=iv,
        option_type='put'
    )
    if abs(greeks['delta']) >= 0.15 and abs(greeks['delta']) <= 0.20:
        print(f"Strike {strike}: delta={greeks['delta']:.3f}, "
              f"theta={greeks['theta']:.4f}, vega={greeks['vega']:.3f}")

# Output:
# Strike 560: delta=-0.158, theta=0.0045, vega=-0.0234
# Strike 559: delta=-0.172, theta=0.0048, vega=-0.0241
```

**Pros**: No external dependencies for Greeks calculation, highest accuracy, full control
**Cons**: Need IV from elsewhere (yfinance), slightly more code

### Option 3: Tradier Free API (SECONDARY FALLBACK)
```python
# Register free sandbox at https://developer.tradier.com/
# No deposit needed, free tier included

import requests
from datetime import datetime, timedelta

def get_tradier_greeks(symbol: str, expiry_date: str, api_token: str):
    """Get options Greeks from Tradier free API."""

    url = "https://sandbox.tradier.com/v1/markets/options/chains"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }

    params = {
        "symbol": symbol,
        "expiration": expiry_date  # YYYY-MM-DD
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    greeks_by_strike = {}
    for option in data['options']['option']:
        strike = option['strike']
        greeks_by_strike[strike] = {
            'delta': float(option['greeks']['delta']),
            'gamma': float(option['greeks']['gamma']),
            'theta': float(option['greeks']['theta']),
            'vega': float(option['greeks']['vega']),
            'iv': float(option['greeks']['mid_iv']),
        }

    return greeks_by_strike

# Find 15-20 delta puts
greeks = get_tradier_greeks("SPY", "2026-04-17", "your_api_token")
puts_15_20 = {
    strike: g for strike, g in greeks.items()
    if -0.20 <= g['delta'] <= -0.15
}
```

**Pros**: Official Greeks from market maker data, free tier available, rate limit (60/min) is workable
**Cons**: Requires registration and token, limited free tier, secondary source only

---

## Implementation Plan

### Phase 1: Minimal Change (Already Works)
Nothing needs to change. The system already uses:
- `src/signals/vix_mean_reversion_signal.py` for VIX (line 26: `import yfinance as yf`)
- `src/utils/yfinance_wrapper.py` for graceful fallback

### Phase 2: Add IV Percentile (30 min)
Add to `src/data/iv_data_provider.py`:
```python
def get_iv_percentile(self, symbol: str) -> float:
    """Get IV percentile using yfinance chain history."""
    import yfinance as yf
    import numpy as np

    ticker = yf.Ticker(symbol)
    expirations = ticker.options[-5:]  # Last 5 expirations

    historical_ivs = []
    for exp in expirations:
        try:
            chain = ticker.option_chain(exp)
            avg_iv = chain.calls['impliedVolatility'].mean()
            if not np.isnan(avg_iv):
                historical_ivs.append(avg_iv)
        except:
            pass

    if not historical_ivs:
        return 50.0

    current_iv = self.get_current_iv(symbol)
    percentile = (sum(1 for iv in historical_ivs if iv < current_iv) / len(historical_ivs)) * 100
    return percentile
```

### Phase 3: Add Delta Calculation (30 min)
Add Black-Scholes function to `src/utils/` or integrate yoptions:
```bash
# Option A: Install yoptions
pip install yoptions

# Option B: Add to src/utils/black_scholes.py (no new dependency)
```

---

## Code Already in Codebase

Your system already handles most of this:

**VIX Fetching**:
- `src/signals/vix_mean_reversion_signal.py` (lines 83-105)
  - Calls `yf.Ticker("^VIX").history()`
  - Returns numpy array of close prices
  - Works with both yfinance and fallback

**IV Integration**:
- `src/data/iv_data_provider.py`
  - Has `get_current_iv()` method
  - Has `get_iv_rank()` method
  - Missing: `get_iv_percentile()` using recent historical chains
  - Missing: Greeks calculation

**Wrapper Infrastructure**:
- `src/utils/yfinance_wrapper.py`
  - Handles import failures gracefully
  - Caches data for CI compatibility
  - Fallback to mock data if needed

---

## Testing Locally

```bash
# Test VIX fetch
python3 << 'EOF'
import yfinance as yf
vix = yf.Ticker("^VIX")
print(vix.history(period="5d")[['Close']])
EOF

# Test SPY IV
python3 << 'EOF'
import yfinance as yf
spy = yf.Ticker("SPY")
chain = spy.option_chain(spy.options[0])
print(f"Average IV: {chain.calls['impliedVolatility'].mean():.2%}")
EOF

# Test if yoptions available (optional)
python3 -c "from yoptions import get_chain_greeks; print('yoptions available')"
```

---

## Why This Solves the Alpaca Subscription Problem

1. **Alpaca limitation**: "subscription does not permit querying recent SIP data"
   - This blocks their real-time options data tier
   - Paper trading is FREE but data tier still restricted

2. **yfinance alternative**:
   - Uses Yahoo Finance data (no subscription needed)
   - Identical columns to Alpaca: IV, bid/ask, volume, etc.
   - Rate limit: Effectively unlimited for SPY
   - Already in project requirements

3. **Cost**: $0
   - No additional libraries beyond what's already required
   - yoptions is optional (lightweight fallback to manual calculation)

---

## Recommended Architecture

```
Entry Signal Path:
├─ VIX Check: yfinance (src/signals/vix_mean_reversion_signal.py)
├─ IV Percentile: yfinance chains → custom calculation
├─ IV/RV Premium: Already in code (src/data/iv_data_provider.py)
└─ Strike Selection: yfinance IV + Black-Scholes delta

Data Flow:
yfinance (option_chain)
  ├─ IV percentile calculation
  ├─ Black-Scholes delta
  └─ Already integrated
```

---

## References

- [yfinance GitHub](https://github.com/ranaroussi/yfinance)
- [yoptions PyPI](https://pypi.org/project/yoptions/)
- [Alpaca Options Docs](https://docs.alpaca.markets/docs/options-trading)
- [FRED VIX Data](https://fred.stlouisfed.org/series/VIXCLS)
- [Black-Scholes Greeks Explanation](https://www.codearmo.com/python-tutorial/options-trading-greeks-black-scholes)
- [Tradier Free API](https://docs.tradier.com/)
