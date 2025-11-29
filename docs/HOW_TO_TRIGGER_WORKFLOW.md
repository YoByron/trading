# 🎯 How to Trigger GitHub Actions Workflow

## Quick Guide

**Page**: https://github.com/IgorGanapolsky/trading/actions/workflows/daily-trading.yml

---

## Step 1: Find the Button

Look at the **top-right corner** of the page, near the workflow name "Daily Trading Execution".

You should see a button that says:
```
[Run workflow ▼]
```

**If you DON'T see this button**, look for a yellow banner that says:
> "This workflow is disabled. Enable it by..."

If you see that banner:
1. Click the **green "Enable workflow"** button
2. Then the "Run workflow" button will appear

---

## Step 2: Click "Run workflow"

Click the **"Run workflow"** button (or dropdown arrow next to it).

---

## Step 3: Configure the Run

A dropdown menu will appear with options:

```
Branch: [main ▼]
☐ Force trade

[Cancel]  [Run workflow]
```

**What to do:**
1. ✅ Make sure **"main"** is selected (should be default)
2. ☑️ Optionally check **"Force trade"** if you want to override duplicate execution check
3. ✅ Click the **green "Run workflow"** button at the bottom

---

## Step 4: Watch It Run

After clicking "Run workflow":
1. The page will refresh
2. A **new run** will appear at the top of the list
3. Click on the run to see detailed execution
4. Watch for:
   - ✅ **Green checkmark** = Success!
   - ❌ **Red X** = Failure (click to see error logs)

---

## Visual Guide

```
┌─────────────────────────────────────────────────────────────┐
│  Daily Trading Execution                    [Run workflow ▼]│ ← CLICK HERE
│                                                              │
│  77 workflow runs                                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Daily Trading Execution #77                          │  │
│  │ Manually run by IgorGanapolsky                       │  │
│  │ 2m 59s  main                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  [Previous runs listed below...]                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Button Not Visible?

**Possible reasons:**
1. Workflow is disabled → Look for yellow "Enable workflow" banner
2. No write permissions → Check repository settings
3. Page not fully loaded → Refresh the page

### After Clicking, Nothing Happens?

1. Check browser console for errors (F12)
2. Try refreshing the page
3. Check if you're logged into GitHub
4. Verify you have write access to the repository

---

## What Happens Next?

After triggering:
1. **Workflow starts** (~30 seconds)
2. **Installs dependencies** (~2 minutes) ← This is where it was failing
3. **Runs tests** (~30 seconds)
4. **Executes trading** (~5-10 minutes)
5. **Commits results** (~1 minute)

**Total time**: ~10-15 minutes

---

## Success Indicators

✅ **Green checkmark** = Everything worked!
- Dependencies installed successfully
- Trading executed
- Results committed to repository

❌ **Red X** = Something failed
- Click on the failed run
- Expand the failed step
- Read the error message
- Share the error with me for debugging

---

**Need help?** Share a screenshot of what you see on the page!
