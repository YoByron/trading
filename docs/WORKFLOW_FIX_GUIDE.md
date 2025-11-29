# 🔧 Workflow Fix Guide - Dashboard Not Updating

## Problem
Dashboard shows "Last Updated: 2025-11-21" but today is Nov 24. The GitHub Actions workflow isn't running automatically.

## Root Cause
- **Last execution**: 12 days ago (Nov 11, 2025)
- **Workflow schedule**: Should run at 9:35 AM ET on weekdays
- **Status**: Workflow is NOT running automatically

## Immediate Fix (Choose One)

### Option 1: Manually Trigger Workflow (Easiest) ⭐

1. Go to: https://github.com/IgorGanapolsky/trading/actions
2. Click **"Daily Trading Execution"** workflow
3. Click **"Run workflow"** button (top right)
4. Click **"Run workflow"** again to confirm
5. Wait for workflow to complete (~5-10 minutes)
6. Check dashboard: https://github.com/IgorGanapolsky/trading/wiki/Progress-Dashboard

**This will:**
- ✅ Execute trading (if not already done today)
- ✅ Generate dashboard with latest data
- ✅ Update GitHub Wiki automatically

### Option 2: Manual Dashboard Update (Quick Fix)

```bash
cd /Users/igorganapolsky/workspace/git/apps/trading
python3 scripts/manual_dashboard_update.py
```

Then manually copy the generated file to the wiki:
1. Open: `wiki/Progress-Dashboard.md`
2. Copy all content
3. Go to: https://github.com/IgorGanapolsky/trading/wiki/Progress-Dashboard
4. Click "Edit"
5. Paste and save

### Option 3: Fix Workflow Schedule

The workflow might be disabled or the cron schedule might be wrong.

**Check workflow status:**
1. Go to: https://github.com/IgorGanapolsky/trading/actions/workflows/daily-trading.yml
2. Check if workflow is enabled
3. Check recent runs - are they failing or not running?

**Current cron schedule:**
- `35 14 * * 1-5` = 9:35 AM ET (EST: Nov-Mar) ✅
- **IMPORTANT**: Update to `35 13 * * 1-5` in March when DST changes!

## Why Workflow Isn't Running

### Possible Causes:

1. **Workflow Disabled**
   - GitHub might have disabled it due to inactivity
   - Check: Settings → Actions → Workflow permissions

2. **Schedule Issue**
   - Cron might be wrong for current timezone
   - DST change might have broken it

3. **Repository Inactivity**
   - GitHub disables workflows after 60 days of inactivity
   - Need to trigger manually to reactivate

4. **Permissions Issue**
   - GITHUB_TOKEN might not have wiki write permissions
   - Check workflow permissions in repository settings

## Verification Steps

After fixing, verify:

1. **Dashboard Updated**
   - Visit: https://github.com/IgorGanapolsky/trading/wiki/Progress-Dashboard
   - Check "Last Updated" shows today's date

2. **Workflow Running**
   - Check: https://github.com/IgorGanapolsky/trading/actions
   - Should see runs at 9:35 AM ET on weekdays

3. **Data Current**
   - Dashboard should show latest P/L, trades, metrics

## Prevention

1. **Monitor Workflow Runs**
   - Set up email notifications for workflow failures
   - Check Actions tab weekly

2. **Update Cron Schedule**
   - Mark calendar: Update cron in March (DST change)
   - EST → EDT: Change `35 14` to `35 13`

3. **Add Health Check**
   - Create a workflow that checks if dashboard is stale
   - Alert if not updated in 24 hours

## Current Status

- ✅ Dashboard script: Working
- ✅ Data generation: Current (Nov 24)
- ❌ Workflow automation: Not running (12 days since last execution)
- ⚠️ Wiki update: Stale (Nov 21)

## Next Steps

1. **Immediate**: Manually trigger workflow (Option 1)
2. **Short-term**: Investigate why workflow stopped running
3. **Long-term**: Add monitoring/alerting for workflow health

---

**Quick Command Reference:**

```bash
# Generate dashboard locally
python3 scripts/generate_progress_dashboard.py

# Check duplicate execution
python3 scripts/check_duplicate_execution.py

# Manual dashboard update
python3 scripts/manual_dashboard_update.py
```
