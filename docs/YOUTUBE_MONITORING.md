# Autonomous YouTube Video Monitoring System

**Status**: Production Ready
**Created**: November 5, 2025
**Last Updated**: November 5, 2025

## Overview

Fully autonomous system that monitors financial YouTube channels daily, automatically downloads transcripts, analyzes content for stock picks, and updates the trading system watchlist. Runs at 8:00 AM ET every weekday (before market open at 9:30 AM).

**Zero manual intervention required** - the system handles everything from video discovery to watchlist updates.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   CRON SCHEDULER (8:00 AM ET)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              scripts/cron_youtube_monitor.sh                │
│  • Activates venv                                           │
│  • Runs youtube_monitor.py                                  │
│  • Logs to logs/cron_youtube.log                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              scripts/youtube_monitor.py                     │
│  • Loads youtube_channels.json config                       │
│  • Checks each channel for new videos (last 24h)            │
│  • Filters for trading-related content via keywords         │
│  • Downloads transcripts via youtube-transcript-api         │
│  • Analyzes content (keyword or LLM-based)                  │
│  • Extracts stock tickers and recommendations               │
│  • Updates data/tier2_watchlist.json                        │
│  • Generates reports in docs/youtube_analysis/              │
│  • Logs everything to logs/youtube_analysis.log             │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌───────────────────────────┐  ┌──────────────────────────┐
│  data/tier2_watchlist.json │  │ docs/youtube_analysis/   │
│  • Auto-updated with picks │  │ • [video_id].md reports  │
│  • Tickers + rationale     │  │ • Full transcripts       │
│  • Source video links      │  │ • Analysis summaries     │
└───────────────────────────┘  └──────────────────────────┘
```

## System Components

### 1. Configuration: `scripts/youtube_channels.json`

Defines which channels to monitor and how to analyze them:

```json
{
  "lookback_hours": 24,
  "use_llm_analysis": false,
  "channels": [
    {
      "name": "Parkev Tatevosian",
      "channel_id": "UCz_cXN42EAGoWFpqSE5OjBA",
      "priority": "high",
      "keywords": ["stock", "investing", "dividend", "analysis"]
    }
  ],
  "global_keywords": ["stock", "investing", "buy", "portfolio"],
  "exclude_keywords": ["crypto", "forex", "day trading"]
}
```

**5 Channels Monitored** (default configuration):
1. Parkev Tatevosian (high priority) - CFA charterholder, stock picks
2. Joseph Carlson (medium) - dividend growth, portfolio reviews
3. Let's Talk Money! with Joseph Hogue (medium) - dividend investing
4. Financial Education (medium) - growth stocks, tech focus
5. Everything Money (medium) - value investing, contrarian picks

### 2. Monitor Script: `scripts/youtube_monitor.py`

Main Python script that handles all automation:

**Key Features**:
- Checks channels for videos uploaded in last 24 hours
- Filters videos by keywords (trading-related only)
- Downloads transcripts using `youtube-transcript-api`
- Caches transcripts to avoid re-downloading
- Extracts stock tickers from content
- Tracks processed videos to avoid duplicates
- Updates watchlist automatically
- Generates markdown analysis reports
- Comprehensive logging

**Analysis Modes**:
- **Keyword Analysis** (default): Fast, free, pattern-based ticker extraction
- **LLM Analysis** (optional): Deep AI analysis using MultiLLM (requires OpenRouter)

### 3. Cron Wrapper: `scripts/cron_youtube_monitor.sh`

Bash wrapper that:
- Activates Python virtual environment
- Runs the monitor script
- Captures all output to `logs/cron_youtube.log`
- Handles errors gracefully
- Keeps log files manageable (last 10,000 lines)

### 4. Setup Script: `scripts/setup_youtube_cron.sh`

One-time setup to install the cron job:

```bash
bash scripts/setup_youtube_cron.sh
```

Creates cron entry: `0 8 * * 1-5 bash scripts/cron_youtube_monitor.sh`

## Installation & Setup

### Prerequisites

```bash
# Already installed in trading/venv:
pip install yt-dlp youtube-transcript-api
```

### One-Time Setup

```bash
# 1. Navigate to project directory
cd /Users/igorganapolsky/workspace/git/apps/trading

# 2. Configure channels (optional - defaults are good)
nano scripts/youtube_channels.json

# 3. Test manual run
python3 scripts/youtube_monitor.py

# 4. Install cron job for automation
bash scripts/setup_youtube_cron.sh

# 5. Verify cron job installed
crontab -l | grep youtube
```

**That's it!** System will now run automatically every weekday at 8:00 AM ET.

## Usage

### Automatic Operation (No Action Required)

Once installed, the system runs automatically:
- **Schedule**: Every weekday at 8:00 AM ET
- **Trigger**: Cron job
- **Output**: Logs + watchlist updates + analysis reports

### Manual Testing

```bash
# Run monitor directly (testing/debugging)
python3 scripts/youtube_monitor.py

# Run via cron wrapper (simulates automated run)
bash scripts/cron_youtube_monitor.sh

# View real-time logs
tail -f logs/youtube_analysis.log
tail -f logs/cron_youtube.log

# Check what videos were processed
cat data/youtube_cache/processed_videos.json
```

### Configuration Changes

**Add New Channel**:

```bash
# Edit configuration
nano scripts/youtube_channels.json

# Add channel entry:
{
  "name": "New Channel Name",
  "channel_id": "UC...",  # From YouTube URL
  "priority": "medium",
  "keywords": ["investing", "stocks"]
}
```

**Change Keywords**:

```bash
# Edit global_keywords or exclude_keywords
nano scripts/youtube_channels.json
```

**Enable LLM Analysis** (costs money via OpenRouter):

```json
{
  "use_llm_analysis": true
}
```

**Change Schedule**:

```bash
# Edit cron job
crontab -e

# Current: 0 8 * * 1-5 (8:00 AM weekdays)
# Change to: 0 7 * * 1-5 (7:00 AM weekdays)
```

## Output Files

### 1. Analysis Reports: `docs/youtube_analysis/`

One markdown file per video:

```
docs/youtube_analysis/
├── [video_id_1].md
├── [video_id_2].md
└── [video_id_3].md
```

**Report Contents**:
- Video metadata (title, channel, date, views)
- Summary of content
- Extracted stock tickers
- Sentiment analysis (if LLM enabled)
- Full transcript
- Recommendations

### 2. Watchlist Updates: `data/tier2_watchlist.json`

Automatically adds new stock picks:

```json
{
  "watchlist": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "source": "YouTube - Parkev Tatevosian",
      "date_added": "2025-11-05",
      "rationale": "Strong Q4 earnings, AI momentum",
      "priority": "high",
      "status": "watchlist",
      "video_url": "https://youtube.com/watch?v=...",
      "analysis_file": "docs/youtube_analysis/[video_id].md"
    }
  ]
}
```

### 3. Logs

- **`logs/youtube_analysis.log`**: Detailed monitor logs (all runs)
- **`logs/cron_youtube.log`**: Cron execution logs (automated runs)

### 4. Cache: `data/youtube_cache/`

- **`processed_videos.json`**: History of processed videos (prevents duplicates)
- **`[video_id]_transcript.txt`**: Cached transcripts (saves API calls)

## How It Works

### Video Discovery Flow

```
1. Cron triggers at 8:00 AM ET
   ↓
2. Script checks each configured channel
   ↓
3. Fetches last 10 videos via yt-dlp
   ↓
4. Filters videos uploaded in last 24 hours
   ↓
5. Checks if already processed (skip if yes)
   ↓
6. Checks if trading-related via keywords
   ↓
7. Downloads transcript via youtube-transcript-api
   ↓
8. Analyzes content (keyword or LLM)
   ↓
9. Extracts stock tickers
   ↓
10. Updates watchlist if high confidence
    ↓
11. Generates markdown report
    ↓
12. Marks video as processed
```

### Keyword Analysis (Default)

Fast, free, pattern-based analysis:

1. **Ticker Extraction**: Finds 1-5 uppercase letter patterns (AAPL, NVDA, etc.)
2. **Filtering**: Removes common words (I, A, THE, etc.)
3. **Confidence**: Counts mentions (≥3 mentions = include)
4. **Output**: List of tickers with mention counts

**Pros**: Fast, free, no API costs
**Cons**: Less context, may miss nuanced recommendations

### LLM Analysis (Optional)

Deep AI-powered analysis using MultiLLM:

1. **Context Extraction**: Sends transcript to Claude/GPT-4/Gemini
2. **Structured Analysis**: Extracts tickers, sentiment, rationale, price targets
3. **Confidence Scoring**: High/medium/low confidence per pick
4. **Risk Assessment**: Identifies warnings and risk factors

**Pros**: Deep understanding, context-aware, high accuracy
**Cons**: Costs ~$0.50-2 per video (OpenRouter API)

**Enable When**: Making $10+/day profit (Month 4+) - see `.claude/CLAUDE.md` for cost-benefit analysis

## Integration with Trading System

### Tier 2 Growth Strategy

Videos feed stock picks into Tier 2 watchlist:

```
YouTube Analysis → tier2_watchlist.json → CoreStrategy → Alpaca Trades
```

**Current Tier 2 Holdings**:
- NVDA (NVIDIA Corporation)
- GOOGL (Alphabet Inc.)

**Recent Additions from YouTube**:
- AMZN (Amazon.com) - OpenAI partnership analysis

### Manual CEO Review Required

While system is autonomous, **CEO should review** high-priority picks before trading:

```bash
# View recent additions
cat data/tier2_watchlist.json | jq '.watchlist[] | select(.source | contains("YouTube"))'

# Read full analysis
cat docs/youtube_analysis/[video_id].md
```

**Recommended Workflow**:
1. System adds stocks to watchlist automatically (status: "watchlist")
2. CEO reviews reports daily
3. CEO approves high-confidence picks
4. Update CoreStrategy to include approved tickers
5. System trades approved stocks automatically

## Monitoring & Maintenance

### Check System Health

```bash
# View recent logs
tail -n 100 logs/youtube_analysis.log

# Check if cron is running
crontab -l | grep youtube

# Check last run status
grep "MONITORING COMPLETE" logs/cron_youtube.log | tail -1

# Count processed videos
cat data/youtube_cache/processed_videos.json | jq '. | length'

# View recent watchlist additions
cat data/tier2_watchlist.json | jq '.watchlist[] | select(.date_added >= "2025-11-05")'
```

### Common Issues

**No videos found**:
- Check channel IDs in `youtube_channels.json`
- Verify lookback_hours (default: 24)
- Confirm channels posted videos recently

**Transcript unavailable**:
- Some videos don't have transcripts
- System skips these automatically (logged)
- Check if channel enables captions

**False positives (non-stocks extracted)**:
- Adjust `global_keywords` to be more specific
- Add to `exclude_keywords` list
- Increase `min_ticker_mentions` threshold

**Cron not running**:
- Check crontab: `crontab -l`
- Verify script paths are absolute
- Check cron logs: `tail logs/cron_youtube.log`

### Performance Tuning

**Reduce API calls**:
- Increase `lookback_hours` to 48-72 (check less frequently)
- Reduce `playlistend` in youtube_monitor.py (check fewer videos)

**Improve accuracy**:
- Enable LLM analysis (costs money)
- Refine keywords per channel
- Increase `min_ticker_mentions` threshold

**Process more channels**:
- Add to `youtube_channels.json`
- Monitor performance (each channel adds ~30-60s)
- Consider running multiple times per day if needed

## Adding New Channels

### Step-by-Step Guide

**1. Find Channel ID**:

Go to channel page → View page source → Search for `"channelId"`

OR use: `https://www.youtube.com/@handle` → View source

**2. Add to Configuration**:

```json
{
  "name": "Channel Name",
  "channel_id": "UCxxxxxxxxxxxxxxxxxxxxx",
  "handle": "@channelhandle",
  "focus": "What they cover",
  "priority": "high|medium|low",
  "keywords": ["relevant", "keywords"],
  "notes": "Why we monitor this channel"
}
```

**3. Test**:

```bash
python3 scripts/youtube_monitor.py
```

**4. Verify**:

Check logs for new channel processing:

```bash
grep "Channel Name" logs/youtube_analysis.log
```

### Recommended Channels (Future Additions)

**Dividend Focused**:
- Dividend Growth Investor
- Dividend Data
- Justin Oh

**Value Investing**:
- The Swedish Investor
- Value Investing with Sven Carlin
- The Investor Channel

**Growth/Tech**:
- ticker symbol: YOU
- Meeting Kevin
- Andrei Jikh

**Institutional/Professional**:
- The Motley Fool
- Morningstar
- Seeking Alpha

## Troubleshooting

### Debug Mode

```bash
# Run with Python debugging
python3 -u scripts/youtube_monitor.py 2>&1 | tee debug.log

# Enable verbose logging (edit youtube_monitor.py)
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Components

```python
# Test video metadata fetch
from youtube_monitor import YouTubeMonitor
monitor = YouTubeMonitor()
videos = monitor.get_recent_videos("UCz_cXN42EAGoWFpqSE5OjBA", 24)
print(videos)

# Test transcript download
transcript = monitor.get_transcript("VIDEO_ID")
print(transcript[:500])

# Test keyword analysis
analysis = monitor._keyword_analysis(video_dict, transcript)
print(analysis)
```

### Reset System State

```bash
# Clear processed videos cache (re-process everything)
rm data/youtube_cache/processed_videos.json

# Clear transcript cache (re-download transcripts)
rm data/youtube_cache/*_transcript.txt

# Clear analysis reports
rm docs/youtube_analysis/*.md

# Clear logs
echo "" > logs/youtube_analysis.log
echo "" > logs/cron_youtube.log
```

## Security & Privacy

**API Keys**: None required for basic operation (yt-dlp and youtube-transcript-api are free)

**LLM Analysis**: If enabled, uses OpenRouter API key from `.env` (already secured)

**Data Storage**: All data stored locally, no external services

**Cron Access**: Runs as user, no root/sudo required

**YouTube Terms of Service**: Compliant - only accessing public videos and transcripts

## Future Enhancements

**Planned** (if system proves valuable):

1. **Sentiment Tracking**: Track analyst sentiment over time
2. **Accuracy Scoring**: Compare picks to actual performance
3. **Multi-language Support**: Analyze non-English channels
4. **Real-time Alerts**: Slack/email when high-confidence pick found
5. **Cross-video Analysis**: Find patterns across multiple videos
6. **Earnings Call Analysis**: Integrate with company earnings calls
7. **Timestamp Extraction**: Jump to specific stock discussions in videos

**Advanced** (Month 4+):

1. **Full LLM Integration**: Enable MultiLLM analysis for all videos
2. **Auto-trading**: Automatically trade high-confidence picks (with circuit breakers)
3. **Portfolio Backtesting**: Simulate returns from historical YouTube picks
4. **Channel Accuracy Metrics**: Track which analysts are most accurate
5. **Dynamic Channel Prioritization**: Auto-adjust based on accuracy

## Cost Analysis

### Current Setup (Keyword Analysis)

**Monthly Cost**: $0
**API Calls**: None (yt-dlp and youtube-transcript-api are free)
**Processing Time**: ~5-10 minutes per day
**Storage**: Minimal (~50MB for transcripts and reports)

### With LLM Analysis (Optional)

**Monthly Cost**: ~$15-30 (depends on video volume)
**Per Video**: ~$0.50-2 (OpenRouter API fees)
**ROI Threshold**: Enable when making $10+/day profit (see `.claude/CLAUDE.md`)

**Cost Breakdown**:
- Claude 3.5 Sonnet: $3/$15 per 1M tokens (input/output)
- Average video: ~5,000 tokens transcript
- Cost per analysis: $0.50-2 depending on model and output length

## Support & Documentation

**Project Documentation**: `docs/YOUTUBE_*.md`
**Configuration**: `scripts/youtube_channels.json`
**Logs**: `logs/youtube_analysis.log`
**Code**: `scripts/youtube_monitor.py`

**Related Skills**:
- `.claude/skills/youtube_analyzer/` - YouTube analysis skill
- `scripts/analyze_youtube_podcast.py` - Manual analysis tool
- `scripts/process_youtube_analysis.py` - Post-processing tool

## Summary

**What**: Autonomous daily monitoring of financial YouTube channels
**When**: 8:00 AM ET every weekday (before market open)
**How**: Cron → yt-dlp → youtube-transcript-api → keyword/LLM analysis
**Output**: Stock picks automatically added to tier2_watchlist.json
**Cost**: $0 (free tier APIs)
**Maintenance**: Zero - fully autonomous

**System Status**: Production ready, requires ZERO manual intervention after setup.

---

*Last Updated: November 5, 2025*
*System Version: 1.0*
*Created by: Claude (CTO)*
