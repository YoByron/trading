# Quick Reference Guide

**Last Updated**: November 20, 2025  
**Purpose**: Quick commands and troubleshooting for common operations

---

## 🚀 Common Commands

### Daily Operations

```bash
# Check system health
python3 scripts/monitor_system.py

# View performance dashboard
python3 scripts/performance_dashboard.py --days 7

# Check evaluation results
python3 scripts/evaluation_summary.py

# Verify today's trades
python3 scripts/verify_execution.py

# Run pre-market health check
python3 scripts/pre_market_health_check.py
```

### Testing

```bash
# Test evaluation system
python3 scripts/test_evaluation_system.py

# Run backtest
python3 scripts/run_backtest_now.py

# Test market data provider
python3 -c "from src.utils.market_data import get_market_data_provider; p = get_market_data_provider(); print(p.get_daily_bars('SPY', 60))"
```

---

## 🔍 Troubleshooting

### Workflow Failed

1. **Check GitHub Actions logs**: Actions tab → Failed run → Job logs
2. **Check evaluation summary**: `python3 scripts/evaluation_summary.py`
3. **Check system health**: `python3 scripts/monitor_system.py`
4. **Verify API keys**: Check `.env` file

### No Trades Executed

1. **Check market hours**: Trades only execute 9:35 AM - 4:00 PM ET weekdays
2. **Check health check**: `python3 scripts/pre_market_health_check.py`
3. **Check evaluation alerts**: Look for critical issues
4. **Check system state**: `cat data/system_state.json | jq .meta.last_updated`

### Evaluation Alerts

1. **View summary**: `python3 scripts/evaluation_summary.py`
2. **Check evaluation files**: `ls -lt data/evaluations/`
3. **Review critical issues**: Look for patterns in alerts

---

## 📊 Key Files

### System State
- `data/system_state.json` - Current system state
- `data/performance_log.json` - Historical performance
- `data/evaluations/evaluations_YYYY-MM-DD.json` - Daily evaluations

### Trade Logs
- `data/trades_YYYY-MM-DD.json` - Daily trade logs
- `reports/daily_report_YYYY-MM-DD.txt` - Daily reports

### Configuration
- `.env` - Environment variables (API keys)
- `.github/workflows/daily-trading.yml` - GitHub Actions workflow

---

## 🚨 Common Issues

### Issue: "System state has no timestamp"
**Fix**: Already fixed in `monitor_system.py` - checks `meta.last_updated`

### Issue: "Positions never closed"
**Fix**: `manage_existing_positions()` is called before new trades in `main()`

### Issue: "Evaluation system unavailable"
**Fix**: Check imports - `from src.evaluation.trading_evaluator import TradingSystemEvaluator`

### Issue: "Workflow timeout"
**Fix**: Already fixed - Alpha Vantage timeout set to 90s, workflow timeout increased to 30min

---

## 💡 Pro Tips

1. **Always check evaluation summary after trades** - catches issues immediately
2. **Monitor system health daily** - prevents surprises
3. **Review evaluation alerts** - they show what went wrong
4. **Check system state freshness** - stale data causes bad decisions

---

## 📞 Need Help?

1. Check `docs/TROUBLESHOOTING.md` for detailed guides
2. Review `docs/MISTAKES_AND_LEARNINGS.md` for known issues
3. Check evaluation results for detected patterns
4. Review system monitoring alerts

