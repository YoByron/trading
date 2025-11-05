# Workflow Integration Overview

## Automated Trading System Workflows

This document describes how all GitHub Actions workflows integrate to create a fully autonomous trading system.

## Workflow Architecture

```
Daily Execution Timeline (Eastern Time)
┌─────────────────────────────────────────────────────────────────┐
│  8:00 AM EST   YouTube Video Analysis                           │
│  ├─ Monitor financial YouTube channels                          │
│  ├─ Download & analyze new video transcripts                    │
│  ├─ Extract stock picks and recommendations                     │
│  ├─ Update data/tier2_watchlist.json                            │
│  └─ Commit & push changes to main                               │
│                                                                   │
│  9:30 AM EST   Market Opens                                      │
│                                                                   │
│  9:35 AM EST   Daily Trading Execution                          │
│  ├─ Checkout latest code (includes YouTube updates)             │
│  ├─ Load system state                                            │
│  ├─ Read updated watchlist                                       │
│  ├─ Execute Tier 1 trades (Core ETFs)                           │
│  ├─ Execute Tier 2 trades (Growth stocks from watchlist)        │
│  ├─ Update system state                                          │
│  └─ Upload logs as artifacts                                     │
│                                                                   │
│  Continuous    Dependabot Auto-Merge                             │
│  ├─ Monitor for Dependabot PRs                                   │
│  ├─ Run Pylint checks                                            │
│  ├─ Verify tests pass                                            │
│  └─ Auto-merge if all checks pass                                │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Details

### 1. YouTube Video Analysis (youtube-analysis.yml)

**Schedule**: 8:00 AM EST, Monday-Friday
**Duration**: 15-20 minutes
**Purpose**: Pre-market intelligence gathering

**Process**:
1. Scan configured YouTube channels for videos posted in last 24h
2. Download transcripts using `youtube-transcript-api`
3. Analyze content (keyword or LLM-based)
4. Extract stock tickers, sentiment, price targets
5. Update `data/tier2_watchlist.json` with high-conviction picks
6. Commit changes with `github-actions[bot]`
7. Push to main branch

**Outputs**:
- Updated watchlist file
- Analysis reports in `docs/youtube_analysis/`
- Execution logs in `logs/youtube_analysis.log`
- Cached transcripts in `data/youtube_cache/`

**Cost**: $0 (uses free tier, keyword analysis)

**Documentation**: [docs/YOUTUBE_WORKFLOW.md](YOUTUBE_WORKFLOW.md)

---

### 2. Daily Trading Execution (daily-trading.yml)

**Schedule**: 9:35 AM EST, Monday-Friday
**Duration**: 5-10 minutes
**Purpose**: Execute daily trades

**Process**:
1. Checkout repository (gets latest watchlist from YouTube workflow)
2. Setup Python environment
3. Install dependencies from requirements.txt
4. Load system state from `data/system_state.json`
5. Execute `scripts/autonomous_trader.py`:
   - Tier 1: Core ETF trades ($6/day) - SPY
   - Tier 2: Growth stock trades ($2/day) - from watchlist
6. Update system state with trade results
7. Upload execution logs and system state as artifacts

**Environment Variables**:
- `ALPACA_API_KEY` - Trading API access
- `ALPACA_SECRET_KEY` - Trading API secret
- `OPENROUTER_API_KEY` - (optional) Multi-LLM analysis
- `DAILY_INVESTMENT` - Default: $10
- `PAPER_TRADING` - true/false

**Outputs**:
- Updated `data/system_state.json`
- Trade logs in `data/trades_YYYY-MM-DD.json`
- Execution logs in `logs/`
- Daily CEO report (when implemented)

**Cost**: $0 for paper trading, real costs when live

**Integration**: Automatically uses watchlist updated by YouTube workflow

---

### 3. Pylint (pylint.yml)

**Trigger**: On push to main, pull requests
**Duration**: 2-5 minutes
**Purpose**: Code quality enforcement

**Process**:
1. Checkout code
2. Setup Python 3.11
3. Install dependencies + pylint
4. Run pylint on src/ directory
5. Score threshold: 8.0/10
6. Generate report

**Status**: NON-BLOCKING (continues on failure)
**Reason**: Allows rapid iteration without breaking CI

**Configuration**: `.pylintrc` in project root

---

### 4. Dependabot Auto-Merge (dependabot-auto-merge.yml)

**Trigger**: When Dependabot creates a PR
**Duration**: 3-7 minutes
**Purpose**: Automated dependency updates

**Process**:
1. Wait for all checks to complete
2. Verify PR is from Dependabot
3. Verify all status checks passed
4. Auto-approve PR
5. Enable auto-merge
6. PR automatically merges when checks pass

**Safety**: Only merges if ALL checks pass (including tests)

**Benefits**: Keeps dependencies current without manual intervention

---

## Data Flow

### Watchlist Update Flow
```
YouTube Video
    ↓
youtube-analysis.yml downloads transcript
    ↓
Analyze content (keyword/LLM)
    ↓
Extract stock tickers + rationale
    ↓
Update data/tier2_watchlist.json
    ↓
Commit & push to main
    ↓
daily-trading.yml checks out latest code
    ↓
GrowthStrategy reads watchlist
    ↓
Evaluate stocks for trading
    ↓
Execute trades if criteria met
```

### System State Flow
```
Previous day's system_state.json
    ↓
daily-trading.yml loads state
    ↓
Execute trades
    ↓
Update P/L, positions, metrics
    ↓
Save updated system_state.json
    ↓
Upload as artifact
    ↓
Next day starts with updated state
```

## Integration Points

### 1. Git as Message Bus
- Workflows communicate via git commits
- YouTube workflow pushes at 8:00 AM
- Trading workflow pulls at 9:35 AM
- No manual coordination needed

### 2. JSON as State Store
- `data/system_state.json` - Current portfolio state
- `data/tier2_watchlist.json` - Growth stock candidates
- `data/trades_YYYY-MM-DD.json` - Daily trade log
- All workflows read/write these files

### 3. GitHub Artifacts
- Logs retained for 30 days
- Downloadable for debugging
- Automatic cleanup after retention period

### 4. Secrets Management
- All API keys in GitHub Secrets
- Never committed to repository
- Automatically injected as env vars

## Manual Triggers

All workflows support manual triggering via `workflow_dispatch`:

1. Go to: Actions tab → Select workflow
2. Click "Run workflow"
3. Select branch: `main`
4. Click green "Run workflow" button

**Use Cases**:
- Test after configuration changes
- Retroactive analysis or trading
- Debug issues
- Demo for stakeholders

## Monitoring

### Check Workflow Health
1. Go to: https://github.com/USERNAME/trading/actions
2. View recent runs for each workflow
3. ✅ = Success, ❌ = Failure, ⏸️ = In progress

### Download Logs
1. Click workflow run
2. Scroll to Artifacts section
3. Download zip file
4. Extract and review logs

### Debug Failures
1. Click failed run
2. Expand failed step
3. Review error messages
4. Check environment variables
5. Verify secrets are set

## Cost Analysis

### GitHub Actions Minutes
| Workflow | Minutes/Day | Days/Month | Total/Month | % of Free Tier |
|----------|-------------|------------|-------------|----------------|
| YouTube Analysis | 15-20 | 22 | 330-440 | 16-22% |
| Daily Trading | 5-10 | 22 | 110-220 | 5-11% |
| Pylint | 2-5 | ~30 | 60-150 | 3-7% |
| Dependabot | 5 | ~10 | 50 | 2% |
| **TOTAL** | | | **550-860** | **27-43%** |

**Free Tier**: 2,000 minutes/month
**Current Usage**: 550-860 minutes/month (27-43%)
**Remaining**: 1,140-1,450 minutes/month (57-73%)
**Cost**: $0/month

### API Costs
| Service | Usage | Cost/Month |
|---------|-------|------------|
| Alpaca Paper Trading | Unlimited | $0 |
| OpenRouter (disabled) | 0 calls | $0 |
| YouTube Transcripts | ~20-50 videos | $0 |
| **TOTAL** | | **$0** |

**When LLM enabled**: Add $1-6/month for OpenRouter

## Security

### Secrets Required
```bash
# GitHub Secrets (Settings → Secrets → Actions)
ALPACA_API_KEY=xxx              # Alpaca trading API
ALPACA_SECRET_KEY=xxx           # Alpaca trading secret
OPENROUTER_API_KEY=xxx          # (optional) Multi-LLM analysis
DAILY_INVESTMENT=10.0           # (optional) Override default
GITHUB_TOKEN=xxx                # Automatically provided
```

### Git Identity
- YouTube workflow: `github-actions[bot]`
- Commits visible in history
- No personal credentials exposed

### API Key Safety
- Never in code or logs
- Injected as environment variables
- Automatically masked in workflow output

## Troubleshooting

### YouTube Workflow Issues

**Problem**: No videos found
- Check channel ID in `scripts/youtube_channels.json`
- Verify channel posted in last 24 hours
- Ensure videos have transcripts enabled

**Problem**: Watchlist not updated
- Check `update_watchlist: true` in config
- Verify stock tickers were recognized
- Review logs for errors

**Problem**: Git push failed
- Check GITHUB_TOKEN permissions
- Look for merge conflicts
- Verify no concurrent edits

### Trading Workflow Issues

**Problem**: Trades not executing
- Check market hours (9:30 AM - 4:00 PM EST)
- Verify Alpaca API keys are valid
- Review logs for API errors
- Check account has sufficient buying power

**Problem**: Watchlist not loading
- Verify `data/tier2_watchlist.json` exists
- Check JSON is valid (no syntax errors)
- Ensure YouTube workflow completed successfully

**Problem**: System state corrupted
- Download previous artifact
- Restore `data/system_state.json`
- Re-run workflow

### General Workflow Issues

**Problem**: Workflow not triggering on schedule
- Check cron syntax is correct
- Verify workflow is enabled (Actions tab)
- Check GitHub Actions status (status.github.com)

**Problem**: Dependencies failing to install
- Check requirements.txt is valid
- Verify PyPI packages are available
- Review pip install logs

**Problem**: Secrets not available
- Verify secrets are set (Settings → Secrets)
- Check secret names match exactly
- Ensure secrets are in correct repo

## Future Enhancements

### Short-Term (Weeks)
- [ ] Add Slack/Discord notifications for trades
- [ ] Email daily CEO report
- [ ] Add more YouTube channels
- [ ] Sentiment scoring for watchlist

### Medium-Term (Months)
- [ ] Enable OpenRouter LLM when profitable
- [ ] Real-time monitoring (not just daily)
- [ ] Backtesting workflow
- [ ] Performance analytics dashboard

### Long-Term (Quarters)
- [ ] Multi-strategy orchestration
- [ ] Options trading workflow
- [ ] IPO participation workflow
- [ ] Crowdfunding tracking workflow

## References

- **YouTube Workflow**: [docs/YOUTUBE_WORKFLOW.md](YOUTUBE_WORKFLOW.md)
- **Trading Strategy**: [.claude/CLAUDE.md](../.claude/CLAUDE.md)
- **System Architecture**: [README.md](../README.md)
- **GitHub Actions Docs**: https://docs.github.com/en/actions

---

**Last Updated**: 2025-11-05
**Status**: Production-ready
**Maintainer**: CTO (Claude)
