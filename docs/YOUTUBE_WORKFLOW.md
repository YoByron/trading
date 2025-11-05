# YouTube Video Analysis Workflow

## Overview

Automated GitHub Actions workflow that monitors financial YouTube channels for new videos, downloads transcripts, analyzes content, and updates the trading system's watchlist before market open.

## Workflow Details

### File Location
`.github/workflows/youtube-analysis.yml`

### Schedule
- **Runs**: 8:00 AM EST (12:00 UTC) every weekday (Monday-Friday)
- **Before**: Daily trading workflow (9:35 AM EST)
- **Window**: 1 hour 35 minutes to complete analysis before trading starts

### Workflow Steps

1. **Setup Environment** (1-2 min)
   - Checkout repository with full git history
   - Setup Python 3.11 with pip caching
   - Install dependencies from requirements.txt
   - Install YouTube-specific packages: `youtube-transcript-api`, `yt-dlp`

2. **Create Directories** (<1 min)
   - `data/youtube_cache/` - Transcript cache and processing history
   - `docs/youtube_analysis/` - Detailed analysis reports
   - `logs/` - Execution logs

3. **Run Monitoring** (5-15 min)
   - Execute `scripts/youtube_monitor.py`
   - Check configured channels for new videos (past 24 hours)
   - Download transcripts for trading-related videos
   - Analyze content (keyword or LLM-based)
   - Extract stock tickers and recommendations
   - Update `data/tier2_watchlist.json` with new picks

4. **Commit Changes** (1-2 min)
   - Detect changes to watchlist file
   - Stage watchlist + analysis reports + cache
   - Commit with descriptive message
   - Push to main branch
   - **Bot**: Uses `github-actions[bot]` identity

5. **Upload Artifacts** (1-2 min)
   - Upload execution logs
   - Upload processed video history
   - Upload analysis reports
   - **Retention**: 30 days

## Integration with Trading Workflow

### Timeline
```
8:00 AM EST  → YouTube analysis starts (youtube-analysis.yml)
8:15 AM EST  → Analysis complete, watchlist updated
8:15 AM EST  → Changes committed and pushed to main
9:30 AM EST  → Market opens
9:35 AM EST  → Trading workflow starts (daily-trading.yml)
9:35 AM EST  → Trading workflow checks out LATEST code (includes watchlist updates)
9:40 AM EST  → Trades executed with fresh YouTube insights
```

### How Trading Workflow Gets Updates

The `daily-trading.yml` workflow always checks out the latest code:
```yaml
- name: Checkout repository
  uses: actions/checkout@v4  # Gets latest commit from main
```

This means any commits made by `youtube-analysis.yml` at 8:00 AM are automatically available when `daily-trading.yml` runs at 9:35 AM.

**No manual intervention required** - workflows communicate via git commits.

## Configuration

### Required Secrets
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions (for git push)
- `OPENROUTER_API_KEY` - For LLM-based analysis (optional)

### Monitored Channels
Configured in `scripts/youtube_channels.json`:
```json
{
  "channels": [
    {
      "name": "Parkev Tatevosian",
      "channel_id": "UCz_cXN42EAGoWFpqSE5OjBA",
      "focus": "Stock picks, value investing, dividend stocks",
      "priority": "high"
    }
  ]
}
```

### Analysis Parameters
```json
{
  "analysis_parameters": {
    "min_video_length_seconds": 180,
    "max_video_length_seconds": 3600,
    "min_views": 100,
    "extract_tickers": true,
    "update_watchlist": true,
    "generate_report": true
  }
}
```

## Outputs

### 1. Updated Watchlist
**File**: `data/tier2_watchlist.json`

**Example Addition**:
```json
{
  "ticker": "AMZN",
  "name": "Amazon.com Inc.",
  "source": "YouTube - Parkev Tatevosian (OpenAI Partnership Analysis)",
  "date_added": "2025-11-04",
  "rationale": "$38B OpenAI cloud deal, 15% upside to fair value",
  "priority": "high",
  "status": "watchlist",
  "video_url": "https://www.youtube.com/watch?v=xyz",
  "analysis_file": "docs/youtube_analysis/xyz.md"
}
```

### 2. Analysis Reports
**Location**: `docs/youtube_analysis/{video_id}.md`

**Contains**:
- Video metadata (title, channel, duration, views)
- Summary of key points
- Stock picks with sentiment and confidence
- Full transcript (first 10,000 chars)
- Rationale for each recommendation

### 3. Execution Logs
**Location**: `logs/youtube_analysis.log`

**Contains**:
- Channel scanning results
- Videos found and processed
- Transcript download status
- Analysis results
- Watchlist updates
- Errors and warnings

### 4. GitHub Actions Artifacts
**Available in**: Workflow run page → Artifacts section

**Includes**:
- `youtube-analysis-logs-{run_id}/`
  - Execution log
  - Processed video history
  - Analysis reports

## Manual Trigger

You can manually trigger the workflow:

1. Go to: https://github.com/USERNAME/trading/actions/workflows/youtube-analysis.yml
2. Click "Run workflow"
3. Select branch: `main`
4. Click green "Run workflow" button

**Use Cases**:
- Test workflow after configuration changes
- Retroactive analysis of recent videos
- Debug issues without waiting for scheduled run

## Monitoring & Debugging

### Check Workflow Status
1. Go to: Actions tab → YouTube Video Analysis
2. View recent runs (✅ success, ❌ failure, ⏸️ in progress)
3. Click run to see detailed logs

### Common Issues

**Issue**: No videos found
- **Check**: Channel ID is correct in `youtube_channels.json`
- **Check**: Channel has posted videos in last 24 hours
- **Check**: Videos have transcripts enabled

**Issue**: Transcript download fails
- **Cause**: Video has no transcript (live streams, shorts)
- **Solution**: System skips and logs warning (expected behavior)

**Issue**: Watchlist not updated
- **Check**: `update_watchlist: true` in config
- **Check**: Videos contained recognized stock tickers
- **Check**: Keywords matched trading-related content

**Issue**: Git push fails
- **Cause**: Permission issues or merge conflicts
- **Solution**: Check GITHUB_TOKEN permissions, ensure no concurrent edits

### Logs Location
- **GitHub Actions**: Workflow run page → Job logs
- **Artifacts**: Download `youtube-analysis-logs-{run_id}.zip`
- **Summary**: Last 20 lines shown in "Summary report" step

## Cost Analysis

### GitHub Actions Minutes
- **Free Tier**: 2,000 minutes/month
- **Usage**: ~15 min/day × 22 trading days = 330 min/month
- **Percentage**: 16.5% of free tier
- **Cost**: $0

### OpenRouter API (if LLM enabled)
- **Per Video**: ~$0.05-0.10 (depends on transcript length)
- **Daily**: 1-3 videos = $0.05-0.30/day
- **Monthly**: $1-6/month
- **Status**: Currently disabled (using keyword analysis)

### Total Cost
- **Current**: $0/month (keyword-based analysis)
- **If LLM enabled**: $1-6/month

## Future Enhancements

### Phase 1 (Current)
- ✅ Keyword-based analysis
- ✅ Automatic watchlist updates
- ✅ Transcript caching
- ✅ Analysis report generation

### Phase 2 (Planned)
- [ ] Enable LLM analysis when profitable ($10+/day)
- [ ] Add more financial YouTubers
- [ ] Sentiment scoring (0-100)
- [ ] Entry/exit price recommendations

### Phase 3 (Advanced)
- [ ] Real-time monitoring (not just daily)
- [ ] Video image analysis (thumbnails, charts)
- [ ] Cross-reference with market data
- [ ] Backtesting YouTube signal quality

## Integration with Trading Strategy

### Tier 2 Growth Strategy
- **Allocation**: 20% of daily investment ($2/day)
- **Current Holdings**: NVDA, GOOGL
- **Watchlist**: Updated daily from YouTube analysis

### How Picks Are Used
1. YouTube video analyzed → Stock added to watchlist
2. Trading workflow runs → Reads watchlist
3. Growth strategy evaluates stocks → Checks fundamentals
4. If criteria met → Execute trade
5. Otherwise → Remains on watchlist for monitoring

### Success Criteria
- **High-conviction picks**: Mentioned 3+ times in video
- **Detailed analysis**: Analyst provides specific rationale
- **Price targets**: Entry zones and profit targets mentioned
- **Catalyst**: News or event driving recommendation

## Workflow YAML Reference

**Key Configuration Points**:

```yaml
# Runs weekdays at 8:00 AM EST
schedule:
  - cron: '0 12 * * 1-5'

# Timeout prevents workflow from hanging
timeout-minutes: 20

# Git push configuration
git config --local user.email "github-actions[bot]@users.noreply.github.com"
git config --local user.name "github-actions[bot]"

# Conditional commit (only if changes detected)
if: steps.check_changes.outputs.changed == 'true'

# Artifact retention
retention-days: 30
```

## Maintenance

### Regular Tasks
- **Weekly**: Review workflow logs for errors
- **Monthly**: Check watchlist quality (are picks useful?)
- **Quarterly**: Evaluate if LLM analysis should be enabled

### Configuration Updates
1. Edit `scripts/youtube_channels.json`
2. Commit to main branch
3. Changes take effect on next scheduled run

### Disable Workflow
If you need to temporarily disable:
1. Go to: Actions → YouTube Video Analysis → "..." menu
2. Click "Disable workflow"
3. Re-enable when ready

---

**Generated**: 2025-11-05
**Status**: Production-ready
**Integration**: Fully automated with daily-trading.yml
