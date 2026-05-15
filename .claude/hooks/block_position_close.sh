#!/bin/bash
# HARD BLOCK: CTO cannot close positions
# Only iron-condor-guardian.yml workflow can close positions
# Per LL-306, LL-325: "Trust the guardrails, not the agent"

INPUT="$1"

# Block ANY position closing attempt
if echo "${INPUT}" | grep -qiE "(close_position|close.*position|submit_order.*SELL|submit_order.*BUY.*close|liquidat)"; then
	echo "🚫 HARD BLOCK: Position closing disabled for CTO"
	echo ""
	echo "Only the iron-condor-guardian workflow can close positions."
	echo "This is enforced by LL-306 and LL-325."
	echo ""
	echo "Guardian closes automatically when:"
	echo "  - 50% profit reached"
	echo "  - 200% stop loss hit"
	echo "  - 7 DTE reached"
	echo ""
	echo "You cannot override this. Phil Town Rule #1."
	exit 1
fi

# Block removal of the TRADING_HALTED kill-switch file via shell.
# It is read by src/risk/trade_gateway.py; removing it re-enables trading.
# The Crisis Monitor process auto-clears it when there are zero positions
# (src/safety/crisis_monitor.py) — that path does not go through this hook.
if echo "${INPUT}" | grep -qE '(data/TRADING_HALTED|data/SYSTEM_HALTED|data/trading_halt\.txt)' &&
	echo "${INPUT}" | grep -qE '(\b(rm|mv|unlink|truncate)\b|>)'; then
	echo "🚫 HARD BLOCK: Removal of trading halt file via shell"
	echo ""
	echo "data/TRADING_HALTED is a load-bearing kill-switch read by"
	echo "src/risk/trade_gateway.py. Removing it re-enables trade execution."
	echo ""
	echo "If clearing is intended, do it through crisis_monitor's"
	echo "auto-clear path (zero positions) or explicit CEO override:"
	echo "  touch /tmp/claude_magic_word_authorized && rm data/TRADING_HALTED"
	exit 1
fi
exit 0
