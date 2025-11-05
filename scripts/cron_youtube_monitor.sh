#!/bin/bash
# Autonomous YouTube Video Monitoring Cron Job
# Runs daily at 8:00 AM ET (before market open at 9:30 AM)
#
# Setup: bash scripts/setup_youtube_cron.sh
# Manual: bash scripts/cron_youtube_monitor.sh

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Paths
PYTHON="/usr/bin/python3"
MONITOR_SCRIPT="$SCRIPT_DIR/youtube_monitor.py"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/youtube_analysis.log"
CRON_LOG="$LOG_DIR/cron_youtube.log"

# Create log directory
mkdir -p "$LOG_DIR"

# Log start
echo "========================================" >> "$CRON_LOG"
echo "YouTube Monitor Started: $(date)" >> "$CRON_LOG"
echo "========================================" >> "$CRON_LOG"

# Change to base directory
cd "$BASE_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..." >> "$CRON_LOG"
    source venv/bin/activate
fi

# Run YouTube monitor
echo "Running YouTube monitor..." >> "$CRON_LOG"
$PYTHON "$MONITOR_SCRIPT" >> "$CRON_LOG" 2>&1
EXIT_CODE=$?

# Log result
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ YouTube monitor completed successfully" >> "$CRON_LOG"
else
    echo "❌ YouTube monitor failed with exit code: $EXIT_CODE" >> "$CRON_LOG"
fi

# Log end
echo "Completed: $(date)" >> "$CRON_LOG"
echo "" >> "$CRON_LOG"

# Keep log file manageable (last 10000 lines)
if [ -f "$CRON_LOG" ]; then
    tail -n 10000 "$CRON_LOG" > "$CRON_LOG.tmp"
    mv "$CRON_LOG.tmp" "$CRON_LOG"
fi

# Exit with monitor's exit code
exit $EXIT_CODE
