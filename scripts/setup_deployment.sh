#!/bin/bash
# Setup automated deployment for 9:35 AM ET trading
# Configures launchd on macOS to run advanced trading system

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_FILE="$HOME/Library/LaunchAgents/com.trading.advanced.plist"

echo "================================="
echo "🚀 Advanced Trading System Setup"
echo "================================="
echo ""

# Create launchd plist
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.advanced</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd $PROJECT_DIR && source venv/bin/activate && python3 scripts/pre_market_health_check.py && python3 scripts/advanced_autonomous_trader.py && python3 scripts/daily_report.py</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>35</integer>
        <key>Weekday</key>
        <integer>1</integer>
    </dict>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>35</integer>
        <key>Weekday</key>
        <integer>2</integer>
    </dict>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>35</integer>
        <key>Weekday</key>
        <integer>3</integer>
    </dict>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>35</integer>
        <key>Weekday</key>
        <integer>4</integer>
    </dict>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>35</integer>
        <key>Weekday</key>
        <integer>5</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/launchd_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/launchd_stderr.log</string>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ Created launchd plist: $PLIST_FILE"
echo ""

# Load launchd job
echo "📝 Loading launchd job..."
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo "✅ Launchd job loaded"
echo ""

# Verify
echo "🔍 Verifying setup..."
launchctl list | grep com.trading.advanced

echo ""
echo "================================="
echo "✅ SETUP COMPLETE"
echo "================================="
echo ""
echo "📅 Schedule: Monday-Friday, 9:35 AM ET"
echo "🔄 Workflow:"
echo "   1. Pre-market health check"
echo "   2. Advanced autonomous trader"
echo "   3. Daily report generation"
echo ""
echo "📁 Logs:"
echo "   - stdout: logs/launchd_stdout.log"
echo "   - stderr: logs/launchd_stderr.log"
echo "   - trading: logs/advanced_trading.log"
echo ""
echo "🛠️  Manual Commands:"
echo "   Run now:     python3 scripts/advanced_autonomous_trader.py"
echo "   Health check: python3 scripts/pre_market_health_check.py"
echo "   Daily report: python3 scripts/daily_report.py"
echo "   Unload:      launchctl unload $PLIST_FILE"
echo ""
echo "🚀 System ready for tomorrow's trading!"
echo "================================="

