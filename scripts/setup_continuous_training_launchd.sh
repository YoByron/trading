#!/bin/bash
# Setup launchd daemon for continuous RL training (local backup)
# Runs weekly as backup to GitHub Actions cloud training

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LAUNCHD_DIR="${HOME}/Library/LaunchAgents"

echo "🔧 Setting up continuous training launchd daemon..."
echo ""

# Create LaunchAgents directory if it doesn't exist
mkdir -p "${LAUNCHD_DIR}"

# Create plist for weekly training (Sundays at 3 AM ET = 8 AM UTC)
cat > "${LAUNCHD_DIR}/com.trading.continuous_training.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.continuous_training</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${REPO_ROOT}/venv/bin/python3</string>
        <string>${REPO_ROOT}/scripts/continuous_training.py</string>
        <string>--local-only</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>${REPO_ROOT}</string>
    
    <key>StandardOutPath</key>
    <string>${REPO_ROOT}/logs/launchd_continuous_training_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>${REPO_ROOT}/logs/launchd_continuous_training_stderr.log</string>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${HOME}/.local/bin</string>
        <key>HOME</key>
        <string>${HOME}</string>
    </dict>
    
    <key>StartCalendarInterval</key>
    <array>
        <!-- Sunday at 3 AM ET (8 AM UTC) - Weekly training -->
        <dict>
            <key>Weekday</key>
            <integer>0</integer>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
</dict>
</plist>
EOF

echo "✅ Created ${LAUNCHD_DIR}/com.trading.continuous_training.plist"
echo ""
echo "📋 Next steps:"
echo "   1. Load the daemon:"
echo "      launchctl load ${LAUNCHD_DIR}/com.trading.continuous_training.plist"
echo ""
echo "   2. Check status:"
echo "      launchctl list | grep continuous_training"
echo ""
echo "   3. View logs:"
echo "      tail -f ${REPO_ROOT}/logs/launchd_continuous_training_*.log"
echo ""
echo "   4. Test manually:"
echo "      python3 ${REPO_ROOT}/scripts/continuous_training.py --local-only"
echo ""
echo "🎯 This daemon runs weekly on Sundays as backup to GitHub Actions cloud training"

