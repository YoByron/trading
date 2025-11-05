# GitHub Actions Integration Strategy

## Overview

This document describes how the YouTube analysis and daily trading workflows are integrated in GitHub Actions CI environment.

**Last Updated**: 2025-11-05

---

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY EXECUTION TIMELINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  8:00 AM ET (12:00 UTC) - YouTube Analysis Workflow         │
│       ↓                                                      │
│       ├─ Fetch latest videos from monitored channels        │
│       ├─ Download transcripts                               │
│       ├─ Analyze content (keyword or LLM)                   │
│       ├─ Update tier2_watchlist.json                        │
│       ├─ Validate JSON format                               │
│       ├─ Commit & push watchlist updates                    │
│       └─ Upload analysis reports                            │
│                                                              │
│  9:35 AM ET (13:35 UTC) - Daily Trading Workflow            │
│       ↓                                                      │
│       ├─ Checkout latest code (includes watchlist updates)  │
│       ├─ Validate tier2_watchlist.json exists & valid       │
│       ├─ Check staleness (warn if > 7 days old)             │
│       ├─ Validate system_state.json (warn if > 48hrs old)   │
│       ├─ Execute trading strategy                           │
│       ├─ Commit & push system_state.json updates            │
│       └─ Upload execution logs                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflow 1: YouTube Analysis (`youtube-analysis.yml`)

### Purpose
Autonomous video monitoring system that:
- Monitors 5 professional financial YouTube channels
- Downloads video transcripts
- Analyzes content for stock picks
- Updates tier2_watchlist.json with new recommendations

### Schedule
- **Cron**: `0 12 * * 1-5` (8:00 AM EST weekdays)
- **Runs**: 1 hour 35 minutes BEFORE trading workflow
- **Manual**: Can be triggered via `workflow_dispatch`

### Key Steps

1. **Checkout & Setup**
   - Fetches full git history (`fetch-depth: 0`)
   - Installs Python 3.11 and dependencies
   - Installs YouTube-specific packages (`youtube-transcript-api`, `yt-dlp`)

2. **Execute Monitoring**
   - Runs `scripts/youtube_monitor.py`
   - Monitors configured channels for videos in last 24 hours
   - Downloads transcripts and analyzes content
   - Updates `data/tier2_watchlist.json` with new stock picks

3. **Git Operations**
   - Checks for changes to `tier2_watchlist.json`
   - Commits and pushes updates if changed
   - Also commits YouTube analysis reports and cache files

4. **Artifacts**
   - Uploads analysis reports (`docs/youtube_analysis/*.md`)
   - Uploads execution logs (`logs/youtube_analysis.log`)
   - Uploads processed video cache
   - Retention: 30 days

### Outputs
- `changed`: Boolean indicating if watchlist was updated

---

## Workflow 2: Daily Trading (`daily-trading.yml`)

### Purpose
Executes daily trading strategy using:
- Core ETF strategy (Tier 1): 60% allocation
- Growth stock strategy (Tier 2): 20% allocation
- Uses tier2_watchlist.json updated by YouTube analysis

### Schedule
- **Cron**: `35 13 * * 1-5` (9:35 AM EST weekdays)
- **Trigger**: Also runs when YouTube analysis completes
- **Manual**: Can be triggered via `workflow_dispatch`

### Key Steps

1. **Checkout & Setup**
   - **CRITICAL**: Always fetches from `main` branch to get latest watchlist
   - Uses `ref: main` to ensure fresh checkout
   - Installs Python 3.11 and trading dependencies

2. **Validation Phase** (NEW)
   - **Watchlist Validation**:
     - Checks `data/tier2_watchlist.json` exists
     - Validates JSON format and structure
     - Checks staleness (warns if > 7 days old)
     - Counts holdings and watchlist stocks
     - **FAIL-SAFE**: Allows execution even if empty (uses fallback strategy)

   - **System State Validation**:
     - Checks `data/system_state.json` exists (optional)
     - Validates JSON format if present
     - Checks staleness (warns if > 48 hours old)
     - **FAIL-SAFE**: Allows execution even if missing (will be created)

3. **Execute Trading**
   - Runs `scripts/autonomous_trader.py`
   - Paper trading mode (`PAPER_TRADING: 'true'`)
   - Uses validated watchlist for Tier 2 stock selection

4. **State Management** (NEW)
   - Checks if `system_state.json` changed during execution
   - If changed:
     - Pulls latest from main (with rebase)
     - Handles merge conflicts (keeps trading execution version)
     - Commits and pushes updated state
   - **Conflict Resolution**: Trading execution takes precedence

5. **Artifacts**
   - Uploads execution logs (`logs/*.log`)
   - Uploads updated system state
   - Uploads trade records (`data/trades_*.json`)
   - Retention: 30 days

---

## Integration Points

### 1. Dependency Chain

**YouTube Analysis → Daily Trading**

The trading workflow depends on YouTube analysis via:
```yaml
workflow_run:
  workflows: ["YouTube Video Analysis"]
  types:
    - completed
```

This ensures:
- Trading workflow can trigger after YouTube analysis completes
- Watchlist updates are always available before trading
- No race conditions between workflows

### 2. Git Synchronization

**YouTube Analysis Commits:**
```
data/tier2_watchlist.json          # Stock picks from videos
docs/youtube_analysis/*.md         # Analysis reports
data/youtube_cache/*               # Transcript cache
```

**Trading Workflow Commits:**
```
data/system_state.json             # Account state, performance metrics
```

**Why This Works:**
- Different files modified by each workflow
- No merge conflicts under normal operation
- Trading workflow always pulls latest before execution

### 3. Conflict Resolution

**Scenario**: Both workflows modify files simultaneously

**Resolution Strategy:**
```bash
# Trading workflow handles conflicts
git pull --rebase origin main || {
  # Keep trading execution version (it's the source of truth)
  git checkout --ours data/system_state.json
  git add data/system_state.json
  git rebase --continue
}
```

**Priority**: Trading execution data > YouTube analysis data

---

## File State Management

### Committed to Git

| File | Updated By | Frequency | Purpose |
|------|-----------|-----------|---------|
| `data/tier2_watchlist.json` | YouTube Analysis | When videos found | Stock picks for Tier 2 |
| `data/system_state.json` | Trading Execution | Daily | Account state, metrics |
| `docs/youtube_analysis/*.md` | YouTube Analysis | When videos analyzed | Analysis reports |
| `data/youtube_cache/*` | YouTube Analysis | When videos processed | Transcript cache |

### Not Committed (Artifacts Only)

| File | Purpose | Access |
|------|---------|--------|
| `logs/*.log` | Execution logs | Artifact downloads |
| `data/trades_*.json` | Daily trade records | Artifact downloads |
| `data/manual_investments.json` | Tier 3/4 tracking | Local only |

---

## Validation & Safety Checks

### Pre-Trading Validations

1. **Watchlist Validation**
   - ✅ File exists (FAIL if missing)
   - ✅ Valid JSON format (FAIL if invalid)
   - ✅ Required fields present (meta, holdings/watchlist)
   - ⚠️  Staleness check (WARN if > 7 days, but continue)
   - ⚠️  Empty check (WARN if no stocks, but continue with fallback)

2. **System State Validation**
   - ⚠️  File exists (WARN if missing, continue)
   - ⚠️  Valid JSON format (WARN if invalid, continue)
   - ⚠️  Staleness check (WARN if > 48 hours, but continue)

**Philosophy**: Fail fast on data integrity, but allow execution with warnings on missing/stale data.

### Post-Trading Validations

1. **State Change Detection**
   - Compare `system_state.json` before/after execution
   - Only commit if actually changed
   - Prevents unnecessary commits

2. **Conflict Detection**
   - Check for concurrent modifications
   - Resolve automatically (trading data wins)
   - Log conflicts for review

---

## Local Development vs CI

### Local Development (Cron Jobs)

```bash
# YouTube monitoring (8:00 AM daily)
0 8 * * 1-5 bash scripts/cron_youtube_monitor.sh

# Trading execution (9:35 AM daily)
35 9 * * 1-5 scripts/run_daily_trading.sh
```

**Characteristics:**
- Uses local Python environment
- Logs to local files
- Git operations optional (no auto-commit)
- Faster execution (no container overhead)

### GitHub Actions CI

**Characteristics:**
- Fresh container for each run
- Always pulls latest code
- Automatic git commits
- Artifact storage (30 days)
- No local state persistence

**Trade-offs:**
| Aspect | Local Cron | GitHub Actions |
|--------|-----------|----------------|
| Speed | Faster | Slower (container startup) |
| State | Persistent | Fresh each run |
| Git | Manual | Automatic |
| Logs | Local files | Artifact storage |
| Secrets | .env file | GitHub Secrets |
| Cost | Free (own hardware) | Free (public repos) |

---

## Troubleshooting

### Issue: Watchlist Not Found

**Symptom**: Trading workflow fails with "tier2_watchlist.json not found"

**Solutions:**
1. Check YouTube analysis workflow completed successfully
2. Verify watchlist was committed (check git history)
3. Ensure trading workflow pulled latest main branch
4. Manually trigger YouTube analysis workflow

### Issue: Staleness Warnings

**Symptom**: Warnings about old watchlist or system state

**Solutions:**
1. Check if YouTube analysis ran today (scheduled at 8 AM)
2. Verify trading execution ran yesterday (scheduled at 9:35 AM)
3. Manually trigger workflows to refresh data
4. Review workflow logs for errors

### Issue: Merge Conflicts

**Symptom**: Git push fails due to conflicts

**Solutions:**
1. Workflow automatically resolves conflicts (trading data wins)
2. If auto-resolution fails, check workflow logs
3. Manually merge and commit from local machine
4. Review conflict resolution strategy in workflow YAML

### Issue: Empty Watchlist

**Symptom**: Warning "Watchlist is empty (no stocks tracked)"

**Expected Behavior**: Trading continues with fallback strategy

**Action**:
1. Check YouTube analysis found relevant videos
2. Verify keyword matching in channel configuration
3. Review processed_videos.json cache
4. Consider manually adding stocks to watchlist

---

## Future Enhancements

### Potential Improvements

1. **Parallel Execution**
   - Run YouTube analysis for multiple channels in parallel
   - Use matrix strategy for faster processing

2. **State Persistence**
   - Use GitHub Releases for long-term state storage
   - Archive old data beyond 30-day artifact retention

3. **Notification System**
   - Send Slack/email alerts on failures
   - Report daily P/L to CEO automatically

4. **Advanced Conflict Resolution**
   - Use JSON merge strategy instead of full file replacement
   - Preserve specific fields during conflicts

5. **Performance Optimization**
   - Cache Python dependencies across runs
   - Use minimal Docker images
   - Reduce checkout depth where possible

---

## Key Decisions & Rationale

### Why Commit system_state.json?

**Decision**: YES - Commit after each trading execution

**Rationale**:
- Preserves complete audit trail
- Enables CEO review without local machine access
- Allows rollback to previous states
- Supports multi-environment deployment

**Alternative**: Could use artifacts only, but lose git history benefits

### Why 1.5 Hour Gap Between Workflows?

**Decision**: YouTube at 8:00 AM, Trading at 9:35 AM (1.5 hour gap)

**Rationale**:
- Ensures YouTube analysis completes before trading
- Allows time for watchlist updates to propagate
- Trading execution aligns with market open (9:30 AM ET)
- Buffer for workflow delays or retries

### Why Allow Execution with Stale Data?

**Decision**: WARN but don't FAIL on stale data

**Rationale**:
- Market still operates even if watchlist is old
- Tier 1 (core ETF) strategy doesn't depend on watchlist
- Tier 2 can use fallback stocks (NVDA, GOOGL)
- Better to trade with old data than miss trading day

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Workflow Success Rate**
   - YouTube analysis completion rate
   - Trading execution success rate
   - Target: > 99% success

2. **Data Freshness**
   - Average watchlist age
   - System state update frequency
   - Target: < 24 hours

3. **Execution Time**
   - YouTube analysis duration
   - Trading execution duration
   - Target: < 10 minutes each

### Recommended Alerts

1. **Critical**: Workflow failure 2 days in a row
2. **Warning**: Watchlist > 7 days old
3. **Info**: New stocks added to watchlist

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Trading System Architecture](../README.md)
- [YouTube Analysis System](./youtube_monitoring.md)

---

*Last Updated: 2025-11-05*
*Maintained by: CTO (Claude AI Agent)*
