#!/bin/bash
# Setup Fully Autonomous Trading System
# This script sets up all continuous training and automation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PATH="${REPO_ROOT}/venv/bin/python3"

echo "=" * 70
echo "🚀 SETTING UP FULLY AUTONOMOUS TRADING SYSTEM"
echo "=" * 70
echo ""

# Check if venv exists
if [ ! -f "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "   Create it with: python3 -m venv venv"
    exit 1
fi

echo "✅ Virtual environment found"
echo ""

# Create logs directory
mkdir -p "${REPO_ROOT}/logs"
echo "✅ Logs directory ready"
echo ""

# Setup launchd for continuous RL training (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Setting up macOS launchd daemon for continuous RL training..."

    LAUNCHD_DIR="${HOME}/Library/LaunchAgents"
    mkdir -p "${LAUNCHD_DIR}"

    # Create plist for continuous RL training (every 2 hours)
    cat > "${LAUNCHD_DIR}/com.trading.rl_training.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.rl_training</string>

    <key>ProgramArguments</key>
    <array>
        <string>${VENV_PATH}</string>
        <string>${REPO_ROOT}/scripts/local_rl_training.py</string>
        <string>--continuous</string>
        <string>--interval</string>
        <string>7200</string>
        <string>--use-langsmith</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${REPO_ROOT}</string>

    <key>StandardOutPath</key>
    <string>${REPO_ROOT}/logs/rl_training_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${REPO_ROOT}/logs/rl_training_stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>${HOME}</string>
    </dict>
</dict>
</plist>
EOF

    # Load the daemon
    launchctl unload "${LAUNCHD_DIR}/com.trading.rl_training.plist" 2>/dev/null || true
    launchctl load "${LAUNCHD_DIR}/com.trading.rl_training.plist"

    echo "✅ Launchd daemon installed and started"
    echo "   Will run RL training every 2 hours automatically"
    echo ""
else
    echo "⚠️  Not macOS - skipping launchd setup"
    echo "   Use cron or systemd for Linux"
    echo ""
fi

# Verify GitHub Actions workflows
echo "📋 Checking GitHub Actions workflows..."
echo ""

WORKFLOWS=(
    "daily-trading.yml:Daily Trading (9:35 AM ET weekdays)"
    "rl-training-continuous.yml:RL Training (every 2 hours during market hours)"
    "model-training.yml:LSTM + RL Training (weekly Sundays)"
    "dashboard-auto-update.yml:Dashboard Update (daily after trading)"
)

for workflow_info in "${WORKFLOWS[@]}"; do
    IFS=':' read -r workflow_file description <<< "$workflow_info"
    if [ -f "${REPO_ROOT}/.github/workflows/${workflow_file}" ]; then
        echo "  ✅ ${description}"
    else
        echo "  ⚠️  ${description} - FILE MISSING"
    fi
done

echo ""
echo "=" * 70
echo "✅ AUTONOMOUS SYSTEM SETUP COMPLETE"
echo "=" * 70
echo ""
echo "📊 What You'll See Automatically:"
echo ""
echo "1. GitHub Wiki Dashboard (Progress-Dashboard.md):"
echo "   - Updates daily after trading execution"
echo "   - Shows: P/L, win rate, risk metrics, charts, AI insights"
echo "   - URL: https://github.com/IgorGanapolsky/trading/wiki/Progress-Dashboard"
echo ""
echo "2. LangSmith Dashboard:"
echo "   - All LLM calls traced automatically"
echo "   - RL training runs logged"
echo "   - URL: https://smith.langchain.com"
echo "   - Project: trading-rl-training"
echo ""
echo "3. GitHub Actions:"
echo "   - Daily trading: Every weekday at 9:35 AM ET"
echo "   - RL training: Every 2 hours during market hours"
echo "   - Dashboard: Updates daily after trading"
echo ""
echo "4. Local RL Training (if macOS):"
echo "   - Runs every 2 hours automatically"
echo "   - Logs: logs/rl_training_stdout.log"
echo ""
echo "🎯 ZERO MANUAL WORK REQUIRED"
echo ""
echo "Everything runs automatically. Just check the dashboards!"
echo ""
