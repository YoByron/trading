# Test-Driven Development (TDD) Approach

## Core Principle

**NEVER deploy untested changes to production.**

Every change MUST be verified in a clean test environment matching GitHub Actions (Python 3.11, Ubuntu) BEFORE pushing to main.

## What Went Wrong (Nov 10, 2025)

### The Anti-Pattern That Broke Trust

1. **Assumed Fix Would Work**: Upgraded yfinance without testing
2. **Deployed to Production**: Pushed directly to main branch
3. **Broke Dependencies**: Created conflicts between packages
4. **Made Promises**: Said "tomorrow it'll work" without proof
5. **Repeated Pattern**: Did this TWICE (commits 743d314, fc2d435)

**Result**: Broken CI, no trades executing, CEO lost trust.

## TDD Process Going Forward

### Phase 1: Write Test FIRST
```bash
# Example: Testing yfinance upgrade
cd tests/
cat > test_yfinance_upgrade.py <<EOF
import yfinance as yf
from datetime import datetime, timedelta

def test_yfinance_data_fetching():
    """Verify yfinance returns data for SPY"""
    ticker = yf.Ticker("SPY")
    hist = ticker.history(period="50d")

    assert not hist.empty, "yfinance returned no data"
    assert len(hist) >= 20, f"Expected 20+ days, got {len(hist)}"
    assert "Close" in hist.columns, "Missing Close column"

    print(f"✅ yfinance working: {len(hist)} days of data")

if __name__ == "__main__":
    test_yfinance_data_fetching()
EOF
```

### Phase 2: Verify in Clean Environment
```bash
# Create clean Python 3.11 environment (match GitHub Actions)
conda create -n test-trading python=3.11 -y
conda activate test-trading

# Install dependencies
pip install -r requirements.txt

# Run test
python tests/test_yfinance_upgrade.py
```

### Phase 3: Deploy ONLY if Test Passes
```bash
# If test passes in clean environment:
git add requirements.txt
git commit -m "fix: Upgrade yfinance to 0.2.60 (verified in Python 3.11)"
git push origin main

# If test fails:
# DO NOT PUSH. Fix the issue and repeat from Phase 1.
```

### Phase 4: Verify in CI
```bash
# After pushing, immediately verify CI passes:
gh run list --workflow="Daily Trading Execution" --limit 1
gh run watch <run-id>

# If CI fails:
# - Immediately revert the commit
# - Analyze failure logs
# - Return to Phase 1
```

## TDD Checklist (MANDATORY for ALL Changes)

Before pushing ANY change to main:

- [ ] **Test exists**: Write test that verifies the change works
- [ ] **Clean environment**: Test in Python 3.11 conda environment (not local venv)
- [ ] **Dependencies verified**: `pip install -r requirements.txt` succeeds
- [ ] **Test passes**: Test runs successfully in clean environment
- [ ] **Markets open** (if testing data fetching): Yahoo/Alpaca APIs available
- [ ] **CI verified**: After push, watch GitHub Actions until completion
- [ ] **Rollback plan**: Know how to revert if CI fails

## For Data Fetching Issues Specifically

### The Right Way to Fix yfinance

1. **Research Phase** (parallel agents):
   ```bash
   # Use 3-4 agents to research:
   # - Latest yfinance version and changelog
   # - Alternative free data sources
   # - Known issues with Yahoo Finance API
   # - Python 3.11 compatibility
   ```

2. **Test Phase** (clean environment):
   ```bash
   conda create -n test-yfinance python=3.11 -y
   conda activate test-yfinance

   # Test current version first
   pip install yfinance==0.2.28
   python -c "import yfinance as yf; print(yf.Ticker('SPY').history(period='50d'))"

   # Test proposed version
   pip install --upgrade yfinance>=0.2.60
   python -c "import yfinance as yf; print(yf.Ticker('SPY').history(period='50d'))"

   # Test all dependencies together
   pip install -r requirements.txt  # Should NOT fail
   ```

3. **Integration Phase** (verify with autonomous_trader.py):
   ```bash
   # Test the actual trading script
   export PAPER_TRADING=true
   export DAILY_INVESTMENT=10.0
   export ALPACA_API_KEY=<test-key>
   export ALPACA_SECRET_KEY=<test-secret>

   python scripts/autonomous_trader.py

   # Verify:
   # - No errors
   # - Data fetched successfully
   # - MACD calculation works
   # - Trades placed (if market open)
   ```

4. **Deploy Phase** (only if all tests pass):
   ```bash
   git add requirements.txt scripts/autonomous_trader.py tests/
   git commit -m "fix: Upgrade yfinance to 0.2.60

   Verified in Python 3.11 clean environment:
   - yfinance 0.2.60 fetches data successfully
   - All dependencies install without conflicts
   - autonomous_trader.py executes without errors
   - MACD calculation produces valid signals

   Test run: python tests/test_yfinance_upgrade.py (PASSED)"

   git push origin main
   ```

## Emergency Revert Protocol

If a pushed change breaks CI:

```bash
# 1. Immediately acknowledge the break
echo "🚨 CI BROKEN by commit <sha>. Reverting now."

# 2. Revert the broken commit(s)
git revert --no-edit <bad-commit-sha>
git push origin main

# 3. Verify revert fixes CI
gh run watch <revert-run-id>

# 4. Analyze failure logs
gh run view <failed-run-id> --log-failed > failure_analysis.txt

# 5. Return to Phase 1 (write test first)
```

## Key Lessons from Nov 10, 2025

1. **Markets Closed = Can't Test Data Fetching**
   - Don't push data fetching fixes on Sunday night (8 PM ET)
   - Yahoo Finance might be down for maintenance
   - Wait until market hours to verify real API responses

2. **Dependency Hell is Real**
   - `pip install <new-package>` might work locally
   - But conflict with existing packages in clean environment
   - ALWAYS test with `pip install -r requirements.txt` from scratch

3. **"Tomorrow" Promises = Broken Trust**
   - Never say "it'll work tomorrow" without proof TODAY
   - If I can't verify now, say "I'll test when markets open and report results"
   - Better to delay 24 hours than deploy untested code

4. **One Fix at a Time**
   - Don't fix yfinance + add langchain + modify 10 files simultaneously
   - Each fix should be isolated, tested, and deployed separately
   - Makes rollback easier if something breaks

## TDD Philosophy

**Test-Driven Development is NOT about slowing down.**

It's about:
- **Building confidence**: Each test proves a piece works
- **Preventing regressions**: Tests catch breaking changes
- **Enabling speed**: Confident changes = faster iteration
- **Earning trust**: CEO trusts CTO who delivers working code

**The fastest way to go slow is to repeatedly break production and revert.**

## Next Steps

1. ✅ **Reverted broken commits** (commits 28ebb80, 9a661a4)
2. ⏳ **Waiting for CI verification** (Daily Trading Execution run #19252361898)
3. 🎯 **Tomorrow 9:35 AM ET**: Watch actual trade execution
4. 📊 **Day 8 report**: Verify if double-cron fix (commit ed08085) was sufficient

**If trades still fail tomorrow**: Return to Phase 1, write tests, fix properly.

**If trades succeed tomorrow**: Single-cron fix was enough, yfinance 0.2.28 is fine.

---

**Remember**: TDD is not optional. It's the foundation of trust between CEO and CTO.
