#!/bin/bash
# Setup autonomous YouTube monitoring cron job
# Runs daily at 8:00 AM ET (before market open at 9:30 AM)

echo "🔧 Setting up autonomous YouTube monitoring..."

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create cron job entry
# Runs every weekday at 8:00 AM ET
CRON_JOB="0 8 * * 1-5 bash $SCRIPT_DIR/cron_youtube_monitor.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "cron_youtube_monitor.sh"; then
    echo "⚠️  YouTube monitoring cron job already exists!"
    echo "Current crontab:"
    crontab -l | grep cron_youtube_monitor
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ YouTube monitoring cron job added!"
    echo "📅 Will run every weekday at 8:00 AM ET (before market open)"
fi

echo ""
echo "📋 Current YouTube monitoring cron job:"
crontab -l | grep cron_youtube_monitor || echo "No job found"

echo ""
echo "🎯 YouTube monitoring is now FULLY AUTONOMOUS!"
echo ""
echo "To test manually:"
echo "  bash scripts/cron_youtube_monitor.sh"
echo ""
echo "To run monitor directly:"
echo "  python3 scripts/youtube_monitor.py"
echo ""
echo "To view logs:"
echo "  tail -f logs/youtube_analysis.log"
echo "  tail -f logs/cron_youtube.log"
echo ""
echo "To check configuration:"
echo "  cat scripts/youtube_channels.json"
echo ""
echo "To remove cron job:"
echo "  crontab -e"
echo ""
echo "Output files:"
echo "  - Analysis reports: docs/youtube_analysis/"
echo "  - Watchlist updates: data/tier2_watchlist.json"
echo "  - Logs: logs/youtube_analysis.log"
echo ""
