# YouTube Monitoring System - Quick Start Guide

**Created**: November 5, 2025
**System Status**: Production Ready
**Zero Manual Intervention Required**

---

## What Was Built

### Autonomous Daily YouTube Video Monitoring System

A fully automated system that:
- Monitors 5 financial YouTube channels daily at 8:00 AM ET (before market open)
- Automatically downloads and analyzes new trading/investing videos
- Extracts stock tickers and recommendations using keyword analysis
- Updates `data/tier2_watchlist.json` automatically
- Generates markdown analysis reports in `docs/youtube_analysis/`
- Logs all activity for audit trail
- Requires **ZERO manual intervention** after setup

---

## Quick Setup (3 Steps)

### 1. Test the System

```bash
cd /Users/igorganapolsky/workspace/git/apps/trading

# Test manual run
source venv/bin/activate
python3 scripts/youtube_monitor.py

# Should see:
# ✅ Monitoring 5 channels
# ✅ Processing videos found
# ✅ Logs saved
```

### 2. Install Cron Job (One-Time)

```bash
bash scripts/setup_youtube_cron.sh

# Verify installation
crontab -l | grep youtube

# Expected output:
# 0 8 * * 1-5 bash /path/to/scripts/cron_youtube_monitor.sh
```

### 3. Done! No Further Action Needed

System will now run automatically every weekday at 8:00 AM ET.

---

## What It Monitors

**5 Professional Financial Channels**:

1. **Parkev Tatevosian, CFA** (high priority)
   - Focus: Stock picks, value investing, dividend stocks
   - Credentials: CFA charterholder
   - Why: Professional analysis with detailed rationale

2. **Joseph Carlson** (medium priority)
   - Focus: Index investing, dividend growth
   - Why: Daily portfolio updates, transparent tracking

3. **Let's Talk Money! with Joseph Hogue** (medium)
   - Focus: Stock analysis, dividend investing
   - Why: Former equity analyst background

4. **Financial Education** (medium)
   - Focus: Growth stocks, tech analysis
   - Why: High-growth opportunities, large community

5. **Everything Money** (medium)
   - Focus: Value investing, contrarian picks
   - Why: Deep value analysis

---

## Output Files

### 1. Watchlist Updates
**File**: `data/tier2_watchlist.json`

Automatically adds stock picks:
```json
{
  "ticker": "AAPL",
  "source": "YouTube - Parkev Tatevosian, CFA",
  "date_added": "2025-11-05",
  "rationale": "Strong Q4 earnings...",
  "priority": "high",
  "video_url": "https://youtube.com/watch?v=...",
  "analysis_file": "docs/youtube_analysis/[video_id].md"
}
```

### 2. Analysis Reports
**Directory**: `docs/youtube_analysis/`

One markdown file per video with:
- Video metadata (title, channel, views, date)
- Stock tickers extracted
- Transcript summary
- Full transcript (first 10,000 chars)

### 3. Logs
**Files**:
- `logs/youtube_analysis.log` - Detailed monitor logs
- `logs/cron_youtube.log` - Automated run logs

---

## Daily Workflow (Fully Automated)

**8:00 AM ET Every Weekday**:

```
1. Cron triggers → scripts/cron_youtube_monitor.sh
2. Script checks 5 channels for new videos (last 24h)
3. For each new video:
   - Downloads transcript via youtube-transcript-api
   - Analyzes content via keyword extraction
   - Extracts stock tickers (3+ mentions = include)
   - Updates watchlist if high confidence
   - Generates markdown report
   - Caches transcript for future use
4. Logs everything to logs/youtube_analysis.log
5. System shuts down until tomorrow
```

**CEO Review** (manual, when convenient):
```bash
# View recent additions
cat data/tier2_watchlist.json | jq '.watchlist[] | select(.source | contains("YouTube"))'

# Read analysis report
cat docs/youtube_analysis/[video_id].md
```

---

## Configuration

### Change Channels

Edit `scripts/youtube_channels.json`:

```json
{
  "channels": [
    {
      "name": "New Channel",
      "channel_id": "@channelhandle",
      "priority": "high",
      "keywords": ["stock", "investing"]
    }
  ]
}
```

### Change Schedule

Edit cron job:
```bash
crontab -e

# Change from 8:00 AM to 7:00 AM:
# 0 7 * * 1-5 bash /path/to/cron_youtube_monitor.sh
```

### Enable LLM Analysis (Costs Money)

Edit `scripts/youtube_channels.json`:
```json
{
  "use_llm_analysis": true
}
```

**Note**: Only enable when making $10+/day profit (Month 4+). See `.claude/CLAUDE.md` for cost-benefit analysis.

---

## Monitoring & Troubleshooting

### Check System Health

```bash
# View recent logs
tail -100 logs/youtube_analysis.log

# Check last run status
grep "MONITORING COMPLETE" logs/cron_youtube.log | tail -1

# Count processed videos
cat data/youtube_cache/processed_videos.json | jq '. | length'

# Verify cron is installed
crontab -l | grep youtube
```

### Common Issues

**No videos found**:
- Normal if channels haven't posted in last 24h
- Check logs: `tail logs/youtube_analysis.log`
- Test manually: `python3 scripts/youtube_monitor.py`

**Transcript unavailable**:
- Some videos don't have captions/transcripts
- System logs and skips these automatically
- Not an error - expected behavior

**Cron not running**:
- Check crontab: `crontab -l`
- Check cron logs: `tail logs/cron_youtube.log`
- Run manually to test: `bash scripts/cron_youtube_monitor.sh`

---

## System Files

**Core Components**:
```
scripts/
├── youtube_monitor.py              # Main monitoring script (23KB)
├── youtube_channels.json           # Configuration (5 channels)
├── cron_youtube_monitor.sh         # Cron wrapper script
└── setup_youtube_cron.sh           # One-time setup script

docs/
├── YOUTUBE_MONITORING.md           # Full documentation (17KB)
└── youtube_analysis/               # Analysis reports directory

data/
├── tier2_watchlist.json           # Auto-updated watchlist
└── youtube_cache/                 # Transcripts & processed videos

logs/
├── youtube_analysis.log           # Monitor logs
└── cron_youtube.log               # Cron execution logs
```

---

## Cost & Performance

**Current Setup (Keyword Analysis)**:
- **Cost**: $0/month (free APIs)
- **Time**: ~5-10 minutes per day (all 5 channels)
- **Storage**: ~50MB for transcripts + reports
- **Maintenance**: Zero

**With LLM Analysis (Optional)**:
- **Cost**: ~$15-30/month (OpenRouter API)
- **Time**: ~10-20 minutes per day
- **Enable When**: Making $10+/day profit (Month 4+)

---

## Integration with Trading System

**Flow**:
```
YouTube Video → Monitor → Analysis → Watchlist → CEO Review → CoreStrategy → Trades
```

**Current Status**:
- System adds stocks to `tier2_watchlist.json` automatically
- Status: "watchlist" (not traded yet)
- **CEO must approve** high-priority picks before they're traded
- Approved stocks added to CoreStrategy manually

**Future Enhancement** (Month 4+):
- Auto-trading of high-confidence picks (with circuit breakers)
- ML-based accuracy scoring per analyst
- Dynamic channel prioritization

---

## Testing & Validation

**System has been tested**:
- ✅ All 5 channels monitored successfully
- ✅ Video discovery working (found new videos)
- ✅ Transcript downloading functional
- ✅ Keyword analysis extracting tickers
- ✅ Error handling graceful (members-only, no transcript, etc.)
- ✅ Logging comprehensive
- ✅ Cron job setup verified

**Production Ready**: Yes, deploy immediately

---

## Next Steps

### Immediate (Today)

1. **Install cron job**:
   ```bash
   bash scripts/setup_youtube_cron.sh
   ```

2. **Verify cron installed**:
   ```bash
   crontab -l | grep youtube
   ```

3. **Test manual run**:
   ```bash
   python3 scripts/youtube_monitor.py
   ```

### Tomorrow (8:00 AM)

- System will run automatically
- Check logs after 8:10 AM: `tail logs/cron_youtube.log`
- Review any new watchlist additions: `cat data/tier2_watchlist.json`

### Ongoing (Daily)

- **Automated**: System runs, analyzes, updates watchlist
- **Manual Review**: CEO checks new additions when convenient
- **Approval**: CEO approves high-confidence picks for trading

---

## Success Metrics

**System is working correctly when**:
- Cron runs daily at 8:00 AM (check logs)
- New videos are processed when available (not every day)
- Watchlist is updated with stock picks (1-3 per week expected)
- No critical errors in logs (warnings are OK)
- Reports are generated in `docs/youtube_analysis/`

**Expected Volume**:
- **Videos per day**: 1-3 across all 5 channels
- **Stock picks per week**: 3-10 tickers
- **High-confidence picks**: 1-2 per week
- **Transcripts cached**: ~100-200 per month

---

## Summary

### What You Get

✅ **Autonomous daily monitoring** of 5 professional financial YouTube channels
✅ **Automatic stock pick extraction** using keyword analysis
✅ **Auto-updated watchlist** with source attribution
✅ **Detailed analysis reports** for each video
✅ **Comprehensive logging** for audit trail
✅ **Zero maintenance** after initial setup
✅ **$0 monthly cost** (free tier APIs)

### How to Activate

```bash
# 1. Test
python3 scripts/youtube_monitor.py

# 2. Install
bash scripts/setup_youtube_cron.sh

# 3. Verify
crontab -l | grep youtube

# Done!
```

System will now run automatically every weekday at 8:00 AM ET.

---

**Full Documentation**: `/Users/igorganapolsky/workspace/git/apps/trading/docs/YOUTUBE_MONITORING.md`
**Configuration**: `/Users/igorganapolsky/workspace/git/apps/trading/scripts/youtube_channels.json`
**Support**: Read logs at `logs/youtube_analysis.log`

---

*System Version: 1.0*
*Production Ready: Yes*
*Created: November 5, 2025*
*Created by: Claude (CTO)*
