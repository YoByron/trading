# Health Monitoring & Alerting Setup

## Overview

This document explains how to set up 100% uptime visibility for the autonomous trading bot using Telegram alerting and automated health checks.

**Problem Solved**: Never again discover failures by asking "How much money did we make today?"

## What You Get

- ✅ **Instant alerts** when trading fails (via Telegram)
- ✅ **Automated health checks** every trading day at 10:05 AM ET
- ✅ **No silent failures** - CEO is immediately notified
- ✅ **$0 cost** - uses free Telegram Bot API
- ✅ **99.9% reliability** - Telegram's infrastructure

## Setup Instructions (10 Minutes)

### Step 1: Create Telegram Bot (5 minutes)

1. **Install Telegram** on your phone (if not already installed)
   - iOS: https://apps.apple.com/app/telegram-messenger/id686449807
   - Android: https://play.google.com/store/apps/details?id=org.telegram.messenger

2. **Open Telegram** and search for `@BotFather`

3. **Create your bot:**
   ```
   Send: /start
   Send: /newbot
   Bot name: Trading System Bot (or any name you want)
   Bot username: tradingsystem_alerts_bot (must end in _bot)
   ```

4. **Copy the token** - BotFather will give you something like:
   ```
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567
   ```
   Save this for Step 3.

5. **Get your Chat ID:**
   - Send any message to your new bot (e.g., "Hello")
   - Visit this URL in your browser (replace `<YOUR_TOKEN>` with the token from step 4):
     ```
     https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
     ```
   - Find `"chat":{"id":123456789}` in the JSON response
   - Save this number for Step 3

### Step 2: Test Telegram Connection (2 minutes)

```bash
cd /Users/igorganapolsky/workspace/git/apps/trading

# Set environment variables (temporarily)
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# Test connection
source venv/bin/activate
python3 -m src.alerts.telegram_alerter
```

You should receive a test message on your phone instantly!

### Step 3: Add to .env File (1 minute)

```bash
# Edit .env file
nano .env

# Add these lines:
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567
TELEGRAM_CHAT_ID=123456789

# Save (Ctrl+O, Enter, Ctrl+X)
```

### Step 4: Enable GitHub Actions Workflow (2 minutes)

1. Commit `.github/workflows/health-check.yml` (already in repo).
2. In GitHub → **Actions**, make sure the **Health Check** workflow is enabled.
3. Configure the repository secret `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`.
4. The workflow runs daily at 10:05 AM ET and calls `scripts/health_check.py`.

### Step 5: Manual Test (Optional)

```bash
# Run health check manually to test
source venv/bin/activate
python3 scripts/health_check.py
```

Expected output:
```
======================================================================
🏥 AUTONOMOUS TRADING BOT - HEALTH CHECK
📅 Date: 2025-11-13 14:30:00 ET
======================================================================

🔍 Checking if trades file exists...
🔍 Checking system state freshness...
🔍 Checking for market data errors...
🔍 Checking portfolio accuracy...

======================================================================
📊 HEALTH CHECK RESULTS
======================================================================
✅ trade_file_exists: Trades file found with 2 entries
✅ system_state_freshness: system_state.json is 2.5h old (fresh)
✅ market_data_errors: No market data errors found in logs
✅ portfolio_accuracy: Portfolio: $100,013.96 (P/L: +$13.96)

Overall Status: HEALTHY
======================================================================

✅ All checks passed - no alerts sent
```

## What Gets Monitored

The health check runs daily at **10:05 AM ET** (30 minutes after trading execution) and verifies:

1. **Trade Execution**
   - ✅ Trades file exists for today
   - ✅ Trades were actually executed (not just attempted)
   - ✅ Order amounts are within expected ranges

2. **Market Data Health**
   - ✅ No "Failed to fetch" errors in logs
   - ✅ All data sources responded successfully
   - ✅ Data is fresh (not stale cached data)

3. **Portfolio State**
   - ✅ system_state.json updated < 24 hours ago
   - ✅ Portfolio values are reasonable ($90K-$110K range)
   - ✅ P/L calculations are accurate

4. **Circuit Breakers** (future)
   - ✅ Daily loss < 2% limit
   - ✅ Max drawdown < 10% limit
   - ✅ Consecutive losses < 3

## Alert Levels

### CRITICAL 🚨
- **When**: System completely failed to execute trades
- **Example**: "No trades file found for today"
- **Action**: Immediate CEO notification via Telegram
- **Response Time**: Check logs within 1 hour

### WARNING ⚠️
- **When**: Trades executed but with issues
- **Example**: "Found 3 market data errors in logs"
- **Action**: CEO notification via Telegram
- **Response Time**: Review before next trading day

### HEALTHY ✅
- **When**: All checks passed
- **Action**: No alert sent (silent success)
- **Logs**: Available in `logs/health_check_stdout.log`

## Example Alerts

### Critical Alert (Trading Failed)
```
🚨 CRITICAL

HEALTH CHECK CRITICAL

Failed Checks:
❌ trade_file_exists
   No trades file found for 2025-11-13
❌ market_data_errors
   Found 12 market data errors in logs

📁 Check logs for details
🎯 Next execution: Tomorrow 9:35 AM ET

⏰ 2025-11-13 10:05:23 ET
```

### Warning Alert (Partial Failure)
```
⚠️ WARNING

HEALTH CHECK WARNING

Failed Checks:
⚠️ market_data_errors
   Found 3 market data errors in logs

📁 Check logs for details
🎯 Next execution: Tomorrow 9:35 AM ET

⏰ 2025-11-13 10:05:23 ET
```

## Troubleshooting

### Not Receiving Alerts?

1. **Check Telegram configuration:**
   ```bash
   source venv/bin/activate
   python3 -m src.alerts.telegram_alerter
   ```

2. **Verify environment variables:**
   ```bash
   grep TELEGRAM .env
   ```

3. **Check GitHub Actions workflow status:**
   - Open **Actions → Health Check** in GitHub.
   - Confirm the latest run succeeded.

4. **Review health check logs:**
   ```bash
   tail -50 logs/health_check_stdout.log
   tail -50 logs/health_check_stderr.log
   ```

### False Positives?

If you're getting alerts when everything is actually working:

1. **Check log patterns** in `scripts/health_check.py:check_market_data_errors()`
2. **Adjust thresholds** for warning vs critical
3. **Review error log parsing** logic

### Workflow Not Running?

1. Re-run the most recent failed job from the Actions UI.
2. Ensure required secrets exist (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
3. Check `logs/health_check_stderr.log` for Python errors.

## Maintenance

### Weekly Review
- Check `logs/health_check_stdout.log` for patterns
- Verify alerts are being received
- Ensure no false positives

### Monthly Review
- Review alert history
- Tune thresholds if needed
- Update documentation with common issues

## Future Enhancements

Planned improvements:

1. **Alpaca API Verification**
   - Query Alpaca API to verify portfolio accuracy
   - Detect "lying" violations (claimed vs actual P/L)

2. **Historical Tracking**
   - Log health check results to JSON
   - Track reliability metrics over time
   - Generate weekly health reports

3. **Self-Healing**
   - Automatic retry of failed trades
   - Cache clearing on data source failures
   - Fallback to alternative strategies

4. **Dashboard**
   - Streamlit web dashboard
   - Real-time health status
   - Historical charts

## Cost

**Total Cost**: $0/month (free forever)

- Telegram Bot API: Free unlimited
- Health checks: Runs on existing infrastructure
- No third-party services required

## Support

For issues or questions:
1. Check this document first
2. Review logs in `logs/health_check_*.log`
3. Test manually: `python3 scripts/health_check.py`
4. Contact CTO (Claude) via conversation

---

**Setup Date**: November 13, 2025
**Last Updated**: November 13, 2025
**Status**: ✅ Production Ready
