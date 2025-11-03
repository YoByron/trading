#!/bin/bash
# Real-time monitoring of autonomous trading execution

echo "🔍 TRADING SYSTEM EXECUTION MONITOR"
echo "===================================="
echo ""
echo "📅 Current Time: $(date)"
echo "🎯 Next Execution: 9:35 AM EST (Weekdays)"
echo ""

echo "📊 LaunchD Job Status:"
launchctl list | grep com.trading.autonomous || echo "⚠️  Job not loaded"
echo ""

echo "📁 Recent Log Files:"
ls -lht /Users/igorganapolsky/workspace/git/apps/trading/logs/*.log 2>/dev/null | head -5 || echo "No logs yet"
echo ""

echo "💬 Tailing logs (CTRL+C to exit)..."
echo "===================================="
tail -f /Users/igorganapolsky/workspace/git/apps/trading/logs/launchd_stdout.log \
        /Users/igorganapolsky/workspace/git/apps/trading/logs/launchd_stderr.log 2>/dev/null &

TAIL_PID=$!

# Wait for user interrupt
trap "kill $TAIL_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait $TAIL_PID
