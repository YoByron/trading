#!/bin/bash
#
# Claude Code PreToolUse Hook - Protect Critical Trading System Files
#
# This hook runs before Write/Edit operations to prevent accidental
# modification or deletion of critical files that could break the
# validated profitable trading system.
#
# Critical files protected:
# - .env (API credentials)
# - data/system_state.json (trading state)
# - backtest_results_60day.json (validation proof)
# - scripts/autonomous_trader.py (production code)
#

set -euo pipefail

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Extract tool_input using jq (parse JSON)
TOOL_INPUT=$(echo "$HOOK_INPUT" | jq -r '.tool_input // empty')

# Extract file_path from tool_input (handles both Write and Edit)
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // empty')

# If no file_path found, allow operation (not a file operation)
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Convert to relative path for cleaner matching
RELATIVE_PATH="${FILE_PATH#$CLAUDE_PROJECT_DIR/}"

# Critical files that should NEVER be edited
BLOCKED_FILES=(
    ".env"
    "data/system_state.json"
    "backtest_results_60day.json"
)

# Check if file is in blocked list
for BLOCKED in "${BLOCKED_FILES[@]}"; do
    if [[ "$RELATIVE_PATH" == "$BLOCKED" ]]; then
        echo "{\"continue\": false, \"decision\": \"deny\", \"reason\": \"🚫 BLOCKED: $BLOCKED is a critical file. It should not be manually edited.\n\nWhy protected:\n- .env: Contains API credentials, manual edits can corrupt format\n- system_state.json: Modified only by autonomous_trader.py\n- backtest_results_60day.json: Validation proof, must remain unmodified\n\nIf you need to modify this file, ask Igor for approval.\"}" >&1
        exit 2
    fi
done

# Files that require warning before editing (but allow with confirmation)
WARNING_FILES=(
    "scripts/autonomous_trader.py"
    "src/strategies/core_strategy.py"
    "src/core/alpaca_trader.py"
    ".claude/settings.json"
)

# Check if file requires warning
for WARN in "${WARNING_FILES[@]}"; do
    if [[ "$RELATIVE_PATH" == "$WARN" ]]; then
        echo "⚠️  WARNING: Editing $WARN (production code). Ensure changes are thoroughly tested." >&2
        exit 0  # Allow but show warning
    fi
done

# Allow all other operations
exit 0
