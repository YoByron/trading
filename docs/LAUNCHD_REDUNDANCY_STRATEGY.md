# Launchd Redundancy Strategy

**Last Updated**: November 26, 2025
**Purpose**: Provide local macOS launchd daemons as backup/redundancy for GitHub Actions workflows

---

## 🎯 Strategy Overview

**Primary**: GitHub Actions (cloud-hosted, reliable, free)
**Secondary**: Local launchd daemons (backup, runs only if GitHub Actions fails)

### Why Redundancy?

1. **GitHub Actions can fail** - CI/CD issues, rate limits, outages
2. **Your Mac is always on** - Reliable local execution
3. **Zero cost** - Uses existing infrastructure
4. **Fast failover** - Local daemons check GitHub status before running

---

## 🔄 How It Works

### Smart Redundancy Check

Each launchd daemon uses a wrapper script that:
1. Checks if GitHub Actions already ran successfully today
2. If yes → Skip execution (avoid duplicates)
3. If no → Execute as backup

**Example Flow**:
```
9:35 AM ET: GitHub Actions scheduled to run
9:35 AM ET: GitHub Actions executes successfully ✅
9:40 AM ET: Local launchd daemon checks status
9:40 AM ET: Sees GitHub Actions already ran → SKIPS ✅

OR

9:35 AM ET: GitHub Actions scheduled to run
9:35 AM ET: GitHub Actions FAILS ❌
9:40 AM ET: Local launchd daemon checks status
9:40 AM ET: Sees GitHub Actions didn't run → EXECUTES ✅
```

---

## 📋 Configured Daemons

### 1. Daily Trading (`com.trading.autonomous.backup`)

**Schedule**: Weekdays at 9:40 AM ET (5 minutes after GitHub Actions)
**Script**: `scripts/autonomous_trader_with_redundancy.sh`
**Backup For**: `.github/workflows/daily-trading.yml`

**What It Does**:
- Checks if GitHub Actions daily-trading workflow ran successfully
- If not, executes `scripts/autonomous_trader.py` locally
- Logs to `logs/launchd_com.trading.autonomous.backup_*.log`

### 2. Health Check (`com.trading.healthcheck.backup`)

**Schedule**: Weekdays at 10:10 AM ET
**Script**: `scripts/health_check.py`
**Backup For**: Various GitHub Actions health check workflows

**What It Does**:
- Runs comprehensive system health checks
- Verifies API connectivity, portfolio accuracy, etc.
- Logs to `logs/launchd_com.trading.healthcheck.backup_*.log`

### 3. Dashboard Update (`com.trading.dashboard.backup`)

**Schedule**: Daily at 6:00 PM ET
**Script**: `scripts/generate_progress_dashboard.py`
**Backup For**: `.github/workflows/dashboard-auto-update.yml`

**What It Does**:
- Updates progress dashboard
- Generates metrics and charts
- Logs to `logs/launchd_com.trading.dashboard.backup_*.log`

---

## 🚀 Setup Instructions

### Initial Setup

```bash
# Run the setup script (creates all plists)
./scripts/setup_launchd_redundancy.sh

# Load the daemons
launchctl load ~/Library/LaunchAgents/com.trading.autonomous.backup.plist
launchctl load ~/Library/LaunchAgents/com.trading.healthcheck.backup.plist
launchctl load ~/Library/LaunchAgents/com.trading.dashboard.backup.plist
```

### Verify Status

```bash
# List all trading daemons
launchctl list | grep trading

# Check specific daemon
launchctl list com.trading.autonomous.backup
```

### View Logs

```bash
# View all launchd logs
tail -f logs/launchd_*.log

# View specific daemon logs
tail -f logs/launchd_com.trading.autonomous.backup_stdout.log
tail -f logs/launchd_com.trading.autonomous.backup_stderr.log
```

### Unload Daemons (if needed)

```bash
launchctl unload ~/Library/LaunchAgents/com.trading.autonomous.backup.plist
launchctl unload ~/Library/LaunchAgents/com.trading.healthcheck.backup.plist
launchctl unload ~/Library/LaunchAgents/com.trading.dashboard.backup.plist
```

---

## 🔍 How Redundancy Check Works

The redundancy check uses `scripts/check_github_actions_status.py`:

1. **Queries GitHub API** via `gh` CLI to check recent workflow runs
2. **Checks if workflow ran today** (successfully, if configured)
3. **Caches results** for 5 minutes to avoid API rate limits
4. **Returns exit code**: 0 = ran today (skip), 1 = didn't run (execute)

**Example**:
```bash
# Check if daily-trading.yml ran today
python3 scripts/check_github_actions_status.py daily-trading.yml

# Output:
# Workflow: daily-trading.yml
# Ran today: True
# Reason: Workflow ran successfully today at 13:35 UTC
```

---

## 📊 Monitoring

### Check Redundancy Status

```bash
# Manual check
python3 scripts/check_github_actions_status.py daily-trading.yml

# View cache
cat data/github_actions_cache.json
```

### Expected Behavior

**Normal Day (GitHub Actions succeeds)**:
```
9:35 AM: GitHub Actions executes ✅
9:40 AM: Local daemon checks → skips (already ran)
Logs show: "GitHub Actions already ran successfully today - skipping local execution"
```

**Failure Day (GitHub Actions fails)**:
```
9:35 AM: GitHub Actions fails ❌
9:40 AM: Local daemon checks → executes backup ✅
Logs show: "GitHub Actions didn't run successfully today - executing local backup"
```

---

## ⚙️ Configuration

### Environment Variables

Launchd daemons inherit environment from your shell. Ensure:
- `.env` file is in repo root (for API keys)
- `venv` is activated (or use full path to venv Python)
- `gh` CLI is installed and authenticated (for GitHub status checks)

### Schedule Adjustments

Edit plist files to change schedules:
```bash
# Edit plist
nano ~/Library/LaunchAgents/com.trading.autonomous.backup.plist

# Reload after editing
launchctl unload ~/Library/LaunchAgents/com.trading.autonomous.backup.plist
launchctl load ~/Library/LaunchAgents/com.trading.autonomous.backup.plist
```

---

## 🛡️ Safety Features

1. **No Duplicate Execution**: Checks GitHub status before running
2. **5-Minute Delay**: Local daemons run 5 minutes after GitHub Actions (allows time for completion)
3. **Cache Protection**: API calls cached to avoid rate limits
4. **Graceful Failures**: If GitHub API unavailable, assumes backup should run (safer)

---

## 🔧 Troubleshooting

### Daemon Not Running

```bash
# Check if loaded
launchctl list | grep trading

# Check logs for errors
tail -f logs/launchd_*_stderr.log

# Manually test script
./scripts/autonomous_trader_with_redundancy.sh
```

### GitHub Status Check Failing

```bash
# Verify gh CLI installed
gh --version

# Verify authenticated
gh auth status

# Test manual check
python3 scripts/check_github_actions_status.py daily-trading.yml
```

### Duplicate Executions

If both GitHub Actions and local daemon run:
1. Check GitHub Actions status check is working
2. Verify cache file exists: `data/github_actions_cache.json`
3. Check logs for redundancy check output

---

## 📈 Benefits

✅ **Reliability**: Never miss a trading day due to GitHub Actions failures
✅ **Zero Cost**: Uses existing Mac infrastructure
✅ **Smart**: Only runs when needed (no duplicates)
✅ **Transparent**: Clear logging shows why backup ran or skipped
✅ **Maintainable**: Easy to add more workflows as backups

---

## 🎯 Best Practices

1. **Keep GitHub Actions as primary** - It's more reliable and provides better audit trail
2. **Monitor logs regularly** - Check if backups are running (indicates GitHub Actions issues)
3. **Update schedules together** - When changing GitHub Actions schedule, update launchd too
4. **Test redundancy** - Periodically disable GitHub Actions to verify backups work
5. **Review cache** - Check `data/github_actions_cache.json` if status checks seem wrong

---

**CTO**: Claude (AI Agent)
**CEO**: Igor Ganapolsky
