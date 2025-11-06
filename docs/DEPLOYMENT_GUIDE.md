# 🚀 DEPLOYMENT GUIDE - 2025 Multi-Agent Trading System

## QUICK START (Tomorrow Morning)

### **Option A: Automated (Recommended)**

```bash
# One-time setup
cd /Users/igorganapolsky/workspace/git/apps/trading
./scripts/setup_deployment.sh

# System will auto-run Monday-Friday at 9:35 AM ET
```

### **Option B: Manual Execution**

```bash
cd /Users/igorganapolsky/workspace/git/apps/trading
source venv/bin/activate

# 1. Health check (REQUIRED before trading)
python3 scripts/pre_market_health_check.py

# 2. Execute trading
python3 scripts/advanced_autonomous_trader.py

# 3. Generate report
python3 scripts/daily_report.py
```

---

## 🛡️ SAFETY SYSTEMS

### **1. Pre-Market Health Check**
Validates BEFORE trading:
- ✅ Alpaca API connectivity
- ✅ Anthropic API status (with fallback)
- ✅ Market status
- ✅ Circuit breakers not tripped
- ✅ Data directories accessible
- ✅ Dependencies present

**CRITICAL:** Must pass before trading is allowed.

### **2. Circuit Breakers**
Auto-stops trading on:
- **Daily Loss** > 2% of portfolio
- **Consecutive Losses** ≥ 3 trades
- **API Errors** ≥ 5 per day
- **Position Size** > 10% of portfolio
- **Manual Trip** (emergency kill switch)

**Reset:** Requires manual intervention via script.

### **3. LLM Fallback**
When Anthropic API fails:
- Falls back to pure technical analysis
- MACD + RSI + Volume + MA indicators
- Conservative position sizing (1% of portfolio, max $100)
- System NEVER stops due to LLM issues

### **4. Position Limits**
Hard caps enforced:
- Max 10% portfolio per position
- Max 5% normal risk per trade
- Max 2% daily loss limit
- Kelly Criterion with 50% safety factor

---

## 📊 MONITORING

### **Check Status**
```bash
# Real-time logs
tail -f logs/advanced_trading.log

# Circuit breaker status
python3 -c "from src.safety.circuit_breakers import CircuitBreaker; print(CircuitBreaker().get_status())"

# Today's trades
cat data/trades_$(date +%Y-%m-%d).json

# Daily report
cat reports/daily_report_$(date +%Y-%m-%d).txt
```

### **Key Files to Monitor**
- `logs/advanced_trading.log` - All agent decisions
- `data/trades_YYYY-MM-DD.json` - Trade log
- `data/rl_policy_state.json` - RL learning progress
- `data/circuit_breaker_state.json` - Safety status
- `reports/daily_report_YYYY-MM-DD.txt` - Daily summary

---

## 🚨 EMERGENCY PROCEDURES

### **Kill Switch (Stop Immediately)**
```bash
# Trip circuit breaker manually
python3 -c "from src.safety.circuit_breakers import CircuitBreaker; CircuitBreaker()._trip_breaker('MANUAL', 'User emergency stop')"

# Or unload launchd
launchctl unload ~/Library/LaunchAgents/com.trading.advanced.plist
```

### **Reset Circuit Breaker**
```bash
python3 -c "from src.safety.circuit_breakers import CircuitBreaker; CircuitBreaker().manual_reset(); print('Reset complete')"
```

### **Check What Went Wrong**
```bash
# Last 50 lines of errors
tail -50 logs/advanced_trading.log | grep ERROR

# Circuit breaker details
cat data/circuit_breaker_state.json

# Alpaca account status
python3 scripts/check_alpaca_status.py
```

---

## 📈 PERFORMANCE TRACKING

### **Daily Metrics to Watch**
1. **Win Rate** - Target: >60%
2. **P/L** - Target: Positive and growing
3. **RL States Learned** - Should increase daily
4. **Circuit Breaker Trips** - Should be zero
5. **Fallback Mode Usage** - Monitor LLM availability

### **Weekly Review (Every Sunday)**
```bash
# Run weekly performance analysis
python3 scripts/weekly_review.py

# Compare to targets:
# - Week 1: Beat 0% win rate (old system)
# - Week 2-4: Hit 55%+ win rate
# - Month 2+: Scale to $100+/day
```

---

## 🔧 TROUBLESHOOTING

### **Problem: Anthropic API "Low Credits"**
**Solution:** System automatically uses fallback mode. No action needed.

### **Problem: Circuit Breaker Tripped**
**Steps:**
1. Check `data/circuit_breaker_state.json` for reason
2. Investigate root cause in logs
3. Fix issue (if needed)
4. Manual reset: `python3 -c "from src.safety.circuit_breakers import CircuitBreaker; CircuitBreaker().manual_reset()"`

### **Problem: No Trades Executing**
**Possible Causes:**
1. Market closed → Normal, orders will execute at open
2. All signals rejected → System being conservative (good!)
3. Circuit breaker tripped → Check status
4. Health check failed → Run `scripts/pre_market_health_check.py`

### **Problem: Trades Too Small/Large**
**Check:**
1. Portfolio value correct? (should be ~$100K)
2. Risk parameters in code (default: 1-2% per trade)
3. Circuit breaker position limits (max 10%)

---

## 🎓 UNDERSTANDING THE SYSTEM

### **How Decisions Are Made**

1. **MetaAgent** detects market regime (LOW_VOL, HIGH_VOL, TRENDING, RANGING)
2. **Specialist Agents** analyze in parallel:
   - ResearchAgent: Fundamentals + news
   - SignalAgent: Technical indicators
   - RiskAgent: Position sizing
3. **Weighted Consensus** based on regime
4. **RL Policy** validates/overrides based on learned experience
5. **ExecutionAgent** places order if approved
6. **Learn from Outcome** for next time

### **Agent Activation by Market Regime**

| Regime | Research | Signal | Risk | Strategy |
|--------|----------|--------|------|----------|
| LOW_VOL | 40% | 30% | 20% | Fundamental focus |
| HIGH_VOL | 20% | 20% | 50% | Risk management |
| TRENDING | 20% | 50% | 20% | Follow momentum |
| RANGING | 33% | 33% | 33% | Balanced |

---

## 📋 DEPLOYMENT CHECKLIST

Before going live tomorrow:
- [x] Multi-agent system built
- [x] LLM fallback implemented
- [x] Circuit breakers configured
- [x] Pre-market health check created
- [x] Daily reporting automated
- [x] Launchd/cron configured
- [x] Safety limits set
- [x] Health check passed
- [ ] **Run setup script** (`./scripts/setup_deployment.sh`)
- [ ] **Verify schedule** (`launchctl list | grep trading`)

---

## 🎯 SUCCESS CRITERIA

### **Week 1 (Nov 7-13)**
- [ ] System runs reliably every day
- [ ] Win rate > 0% (beat old system)
- [ ] No circuit breaker trips
- [ ] RL learning functioning

### **Month 1 (Nov 7 - Dec 6)**
- [ ] Win rate > 55%
- [ ] Positive P/L
- [ ] Smooth operation
- [ ] RL showing improvement

### **Month 2-3**
- [ ] Win rate > 60%
- [ ] Scale position sizes
- [ ] Approach $100+/day goal

---

## 🔗 RELATED DOCS

- `2025_MULTI_AGENT_SYSTEM.md` - System architecture
- `PLAN.md` - Overall strategy
- `logs/` - All execution logs
- `data/` - State and trade data

---

**Deployed:** November 6, 2025  
**Status:** Ready for production  
**First Trade:** November 7, 2025, 9:35 AM ET

