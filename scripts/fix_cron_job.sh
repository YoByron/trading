#!/bin/bash
# Fix the cron job to use the virtual environment and correct paths

PROJECT_ROOT="/Users/ganapolsky_i/workspace/git/igor/trading"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"
LOG_FILE="$PROJECT_ROOT/logs/cron.log"

# Define the correct cron command
# Runs every weekday at 9:35 AM ET
CRON_SCHEDULE="35 9 * * 1-5"
CRON_CMD="cd $PROJECT_ROOT && $VENV_PYTHON scripts/autonomous_trader.py >> $LOG_FILE 2>&1"
FULL_CRON_LINE="$CRON_SCHEDULE $CRON_CMD"

echo "🔧 Fixing cron job..."

# Backup current cron
crontab -l > cron_backup.txt 2>/dev/null

# Clean up old/broken entries (matching autonomous_trader)
grep -v "autonomous_trader.py" cron_backup.txt > cron_clean.txt

# Add the new correct entry
echo "$FULL_CRON_LINE" >> cron_clean.txt

# Install new crontab
crontab cron_clean.txt

# Cleanup temp files
rm cron_backup.txt cron_clean.txt

echo "✅ Cron job updated:"
crontab -l | grep autonomous_trader.py

echo "📅 Schedule: Weekdays at 9:35 AM ET"
echo "🐍 Python: $VENV_PYTHON"
