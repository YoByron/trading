# 🚨 CRITICAL: Workflow Recovery Guide

## Current Situation

**Status**: Workflow may be disabled or failing
**Last Successful Run**: November 11, 2025
**Missing Days**: Nov 12-15, 18-20 (7 trading days)

## Quick Fix (2 Minutes)

### Step 1: Check Workflow Status

Go to: **https://github.com/IgorGanapolsky/trading/actions/workflows/daily-trading.yml**

**Look for**:
- ✅ Green "Active" badge = Workflow is enabled
- ❌ Yellow "This workflow is disabled" banner = Needs re-enabling

### Step 2: Re-enable if Disabled

If you see the yellow banner:
1. Click **"Enable workflow"** button (green button)
2. Confirm the action

### Step 3: Trigger Today's Trading

1. On the workflow page, click **"Run workflow"** (top right)
2. Select branch: **main**
3. Optionally check **"Force trade"** if you want to override duplicate check
4. Click green **"Run workflow"** button

### Step 4: Verify Execution

1. Watch the run appear in the list
2. Click on the run to see logs
3. Wait 5-10 minutes for completion
4. Check for:
   - ✅ Green checkmark = Success
   - ❌ Red X = Failure (check logs)

## What Happens After Fix

✅ **Tomorrow (Nov 21)**: Workflow automatically runs at 9:35 AM EST
✅ **Every Weekday**: Scheduled execution resumes
✅ **No Code Changes**: Everything is already configured correctly

## Why This Happened

GitHub automatically disables scheduled workflows after 60 days of repository inactivity. This is a GitHub security feature to prevent abandoned workflows from running.

## Verification Commands

```bash
# Check workflow status
gh workflow list

# View recent runs
gh run list --workflow=daily-trading.yml --limit 10

# Trigger manually (if you have permissions)
gh workflow run daily-trading.yml

# View workflow details
gh workflow view daily-trading.yml
```

## Impact on 90-Day Challenge

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Days Executed | 16 | 9 | ❌ 44% behind |
| Days Until Nov 30 | - | 7 trading days | ⚠️ Not enough |
| Recommendation | 30 days data | Extend to Dec 15 | ✅ Recommended |

**Recommendation**: Extend Judgment Day from Nov 30 to Dec 15 to get a full 30 days of clean trading data.

## Troubleshooting

### Workflow Shows as Active But Not Running

**Possible Causes**:
1. Schedule disabled (check workflow YAML)
2. Repository secrets missing
3. Workflow file syntax errors
4. GitHub Actions quota exceeded

**Check**:
```bash
# View workflow YAML
gh workflow view daily-trading.yml --yaml

# Check recent failures
gh run list --workflow=daily-trading.yml --limit 5
```

### Workflow Runs But Fails

**Check Logs**:
1. Go to Actions tab
2. Click on failed run
3. Expand failed step
4. Read error message

**Common Issues**:
- Missing API keys (check Secrets)
- Python dependency errors
- Test failures
- Timeout issues

## Next Steps After Recovery

1. ✅ Monitor next few runs to ensure stability
2. ✅ Check daily reports for execution confirmation
3. ✅ Verify system_state.json updates
4. ✅ Consider extending challenge period

---

**Bottom Line**: The fix is simple - just click 2 buttons in GitHub UI. The workflow is configured correctly, it just needs to be re-enabled.
