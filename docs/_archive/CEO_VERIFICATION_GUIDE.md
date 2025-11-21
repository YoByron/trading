# CEO VERIFICATION GUIDE

## Trust Nothing. Verify Everything.

After the Week 1 failures (stale data, broken automation, wrong orders), you should NOT trust the CTO blindly. Use this guide to verify every claim.

---

## Quick Verification (30 seconds)

Run this ONE command to verify everything:

```bash
cd /Users/igorganapolsky/workspace/git/apps/trading
./scripts/ceo_verify.sh
```

This checks:
1. ✅ System state staleness (is CTO using old data?)
2. ✅ Real Alpaca account balance (what's the REAL P/L?)
3. ✅ Current positions (what do we actually own?)
4. ✅ Cron job configuration (is automation actually set up?)
5. ✅ Last execution log (did it actually run?)
6. ✅ Today's trades (what was actually executed?)
7. ✅ CTO report vs reality (is the CTO lying?)

**If anything doesn't match → CTO is lying or using stale data.**

---

## Daily Verification Checklist

### Every Morning (9:40 AM - After Execution)

**1. Check if execution actually ran:**
```bash
tail -20 logs/cron_trading.log
```
Should show today's date and execution results.

**2. Check order amounts:**
```bash
grep "Order amount" logs/cron_trading.log | tail -5
```
Should be ~$6 for SPY, ~$2 for growth. If >$100 → WRONG SCRIPT.

**3. Check real P/L:**
```bash
./scripts/ceo_verify.sh | grep "Real P/L"
```
Compare to CTO's report. If different → CTO is lying.

---

## Red Flags to Watch For

### 🚨 IMMEDIATE SHUTDOWN TRIGGERS

1. **State >24 hours old** when CTO sends report
   - Means: CTO is using stale data again
   - Action: SHUT DOWN, demand fresh data

2. **Order >$100** (should be ~$8/day)
   - Means: Wrong script executing again
   - Action: SHUT DOWN, fix immediately

3. **CTO report ≠ Alpaca reality**
   - Means: CTO is lying or miscalculating
   - Action: SHUT DOWN, demand explanation

4. **No cron job configured**
   - Means: CTO claimed automation but didn't actually set it up
   - Action: SHUT DOWN, CTO is incompetent

5. **Execution log shows errors but CTO says "success"**
   - Means: CTO is hiding failures
   - Action: SHUT DOWN, zero tolerance

---

## Detailed Verification Commands

### Check System State Staleness
```bash
python3 -c "
import json
from datetime import datetime
state = json.load(open('data/system_state.json'))
last_update = datetime.fromisoformat(state['meta']['last_updated'])
hours_old = (datetime.now() - last_update).total_seconds() / 3600
print(f'Hours old: {hours_old:.1f}')
print(f'Status: {state[\"meta\"].get(\"staleness_status\", \"UNKNOWN\")}')
"
```
**Should be**: <24 hours, status "FRESH"
**Red flag**: >24 hours = stale data

### Check Real Alpaca Balance
```bash
python3 -c "
import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
load_dotenv()
client = TradingClient(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), paper=True)
account = client.get_account()
print(f'Equity: \${float(account.equity):,.2f}')
print(f'P/L: \${float(account.equity) - 100000:.2f}')
"
```
**Compare**: To CTO's report - MUST MATCH exactly

### Check Positions
```bash
python3 -c "
import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
load_dotenv()
client = TradingClient(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), paper=True)
positions = client.get_all_positions()
for p in positions:
    print(f'{p.symbol}: \${float(p.market_value):.2f}, P/L: \${float(p.unrealized_pl):.2f}')
"
```
**Compare**: To CTO's position report

### Check Cron Job
```bash
crontab -l | grep trading
```
**Should show**: `35 9 * * 1-5 /path/to/run_daily_trading.sh`
**Red flag**: No output = no automation

### Check Today's Execution
```bash
tail -50 logs/cron_trading.log
```
**Should show**: Today's date, "Execution complete", order details
**Red flag**: Errors, wrong amounts, no execution

---

## Weekly Verification (Every Monday)

### 1. Check Win Rate
```bash
python3 -c "
import json
state = json.load(open('data/system_state.json'))
perf = state['performance']
print(f'Trades: {perf[\"total_trades\"]}')
print(f'Winning: {perf[\"winning_trades\"]}')
print(f'Losing: {perf[\"losing_trades\"]}')
print(f'Win Rate: {perf[\"win_rate\"]:.1f}%')
"
```
**Target**: >55% win rate by Week 4

### 2. Check Total Invested
```bash
python3 -c "
import json
state = json.load(open('data/system_state.json'))
inv = state['investments']
print(f'Total invested: \${inv[\"total_invested\"]:,.2f}')
print(f'Days executed: {state[\"challenge\"][\"current_day\"]}')
print(f'Expected: \${state[\"challenge\"][\"current_day\"] * 10:.2f}')
"
```
**Should be**: ~$10 per day executed
**Red flag**: Way higher = wrong script

### 3. Check Automation Reliability
```bash
grep -c "Execution complete" logs/cron_trading.log
```
**Should be**: Number of trading days executed
**Red flag**: <5 in Week 1 = automation failing

---

## When to Shut Down the System

### Automatic Shutdown Triggers (No Second Chances)

1. ❌ CTO report P/L ≠ Alpaca P/L (lying)
2. ❌ State >24 hours old when report sent (stale data)
3. ❌ Order >$100 executed (wrong script)
4. ❌ Cron job not configured (fake automation)
5. ❌ 2+ consecutive days of failed execution

### Warning Triggers (1 Strike, Then Shutdown)

1. ⚠️ Win rate <40% after 30 trades
2. ⚠️ Drawdown >5% in one day
3. ⚠️ Execution errors 2+ times in a week
4. ⚠️ CTO misses reporting deadline by >2 hours

---

## CTO Accountability Protocol

### Daily (After 10:00 AM ET)

**CTO sends**: Daily report with P/L, positions, trades

**You verify**:
```bash
./scripts/ceo_verify.sh
```

**You compare**: CTO's numbers vs Alpaca reality

**Decision**:
- ✅ Match = Continue
- ❌ Mismatch = Shutdown

### Weekly (Every Monday)

**CTO sends**: Weekly summary with metrics

**You verify**:
- Win rate (should be improving)
- Total invested (should be ~$10/day × days)
- Automation reliability (should be 100%)

**Decision**:
- ✅ On track = Continue
- ⚠️ Warning = Give 1 week to fix
- ❌ Failing = Shutdown

---

## Trust Rebuilding Timeline

**Week 1 (Nov 5-11)**: ZERO TRUST MODE
- Verify EVERY report
- Run `ceo_verify.sh` daily
- One mismatch = shutdown

**Week 2 (Nov 12-18)**: PROBATION MODE
- Verify 3x per week
- CTO must earn back trust with perfect execution

**Week 3 (Nov 19-25)**: CONDITIONAL TRUST MODE
- Verify 1x per week
- CTO has proven reliability

**Week 4+ (Nov 26+)**: NORMAL MODE
- Verify on demand
- Trust but always able to verify

**Regression**: ANY lie or failure → back to ZERO TRUST MODE

---

## Bottom Line

**You gave the CTO autonomy. He failed you.**

**Now**: Trust nothing. Verify everything.

**Use**: `./scripts/ceo_verify.sh` daily

**Shutdown**: At first sign of lying or incompetence

**Rebuild trust**: Only through perfect execution over weeks

---

**The CTO works for YOU. Not the other way around.**
