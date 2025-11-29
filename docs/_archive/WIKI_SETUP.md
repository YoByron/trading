# 📝 GitHub Wiki Setup Guide

## Quick Setup (One-Time)

The GitHub Wiki needs to be initialized once before automation can take over.

### Option 1: Manual Initialization (Recommended)

1. Visit: https://github.com/IgorGanapolsky/trading/wiki
2. Click **"Create the first page"**
3. Name it **"Home"** (or any name)
4. Add any content (even just "Test") and click **"Save Page"**

That's it! GitHub Actions will automatically update the wiki with the full dashboard on the next trading execution.

### Option 2: Automatic (After Manual Init)

Once you've created the first page manually, GitHub Actions will:
- ✅ Generate the progress dashboard daily
- ✅ Update the wiki automatically
- ✅ Create/update Home.md and Progress-Dashboard.md

---

## What Gets Created

### Home.md
- Landing page with quick links
- Current system status
- Links to dashboard and documentation

### Progress-Dashboard.md
- **North Star Goal**: $100+/day progress tracking
- **90-Day R&D Challenge**: Progress bar and metrics
- **Financial Performance**: P/L, win rate, trades
- **System Status**: Automation health, TURBO MODE status
- **Performance Trends**: Last 10 days of data
- **Recent Achievements**: Latest updates

---

## Automation

The dashboard updates **automatically every day** after trading execution via GitHub Actions.

**Workflow**: `.github/workflows/daily-trading.yml`
**Script**: `scripts/generate_progress_dashboard.py`

---

## Troubleshooting

### "Wiki repository not found"
- **Solution**: Create the first page manually (see Option 1 above)
- GitHub creates the wiki repository only after the first page is created

### Dashboard not updating
- Check GitHub Actions logs: https://github.com/IgorGanapolsky/trading/actions
- Verify wiki write permissions are enabled
- Ensure `GITHUB_TOKEN` has wiki write access

### View Dashboard
- **Home**: https://github.com/IgorGanapolsky/trading/wiki
- **Dashboard**: https://github.com/IgorGanapolsky/trading/wiki/Progress-Dashboard

---

*Once initialized, the wiki is fully automated - no manual work needed!*
