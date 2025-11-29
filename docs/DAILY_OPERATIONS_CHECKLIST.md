# Daily Operations Checklist

**Last Updated**: November 20, 2025
**Purpose**: Ensure consistent daily operations and catch issues early

---

## 🌅 Morning Routine (Before Market Open)

### Pre-Market Checks (8:00 AM ET)

- [ ] **System Health Check**
  ```bash
  python3 scripts/monitor_system.py
  ```
  - Verify system state freshness (<24h old)
  - Check performance log updated
  - Review any alerts

- [ ] **Pre-Market Health Check**
  ```bash
  python3 scripts/pre_market_health_check.py
  ```
  - API connectivity verified
  - Market status checked
  - Data sources available

- [ ] **Pre-Flight Check** (if manual run)
  ```bash
  python3 scripts/preflight_check.py
  ```
  - Environment variables set
  - Code fixes verified
  - System ready

---

## 📊 During Trading Hours (9:35 AM - 4:00 PM ET)

### Trade Execution Monitoring

- [ ] **Check GitHub Actions** (if automated)
  - Workflow started successfully
  - No timeout errors
  - Trades executed

- [ ] **Review Evaluation Alerts** (if any)
  ```bash
  python3 scripts/evaluation_summary.py
  ```
  - Check for critical issues
  - Review error patterns
  - Address any alerts

---

## 🌆 End of Day (After Market Close)

### Post-Trading Review

- [ ] **Verify Trade Execution**
  ```bash
  python3 scripts/verify_execution.py
  ```
  - Orders filled correctly
  - Position sizes correct
  - No execution errors

- [ ] **Review Performance**
  ```bash
  python3 scripts/performance_dashboard.py --days 1
  ```
  - Today's P/L
  - Win rate update
  - System reliability

- [ ] **Check Evaluation Results**
  ```bash
  python3 scripts/evaluation_summary.py
  ```
  - Review detected issues
  - Check error patterns
  - Note any trends

- [ ] **System Health Check**
  ```bash
  python3 scripts/monitor_system.py
  ```
  - Verify all systems healthy
  - Check for warnings
  - Review metrics

---

## 📅 Weekly Review (Every Monday)

- [ ] **Weekly Performance Summary**
  ```bash
  python3 scripts/performance_dashboard.py --days 7
  ```

- [ ] **Review Evaluation Patterns**
  ```bash
  python3 scripts/evaluation_summary.py
  ```
  - Look for recurring issues
  - Check error pattern trends
  - Identify improvements

- [ ] **System Reliability Check**
  - Review data gaps
  - Check automation status
  - Verify all systems operational

---

## 🚨 When Issues Detected

### Critical Issues (Immediate Action)

1. **Order Size Error** (>10x expected)
   - Check evaluation summary
   - Review trade logs
   - Verify order validation working

2. **System State Stale** (>24h old)
   - Update system state
   - Check automation status
   - Verify workflow running

3. **Workflow Failed**
   - Check GitHub Actions logs
   - Review error messages
   - Fix and re-run if needed

### Non-Critical Issues (Monitor)

1. **Network/DNS Errors**
   - Check API status
   - Verify retry logic working
   - Monitor for patterns

2. **Data Source Failures**
   - Check fallback working
   - Review data source metrics
   - Consider alternative sources

---

## 💡 Pro Tips

1. **Automate What You Can**: Most checks run automatically via GitHub Actions
2. **Check Evaluation First**: Evaluation summary shows issues immediately
3. **Monitor Patterns**: Look for recurring issues in evaluation results
4. **Document Issues**: Add to `docs/MISTAKES_AND_LEARNINGS.md` when found

---

## 🔗 Quick Links

- **System Health**: `python3 scripts/monitor_system.py`
- **Performance**: `python3 scripts/performance_dashboard.py`
- **Evaluations**: `python3 scripts/evaluation_summary.py`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Quick Reference**: `docs/QUICK_REFERENCE.md`
