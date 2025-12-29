#!/bin/bash
#
# Claude Code SessionStart Hook - Process Pending Feedback
#
# This hook processes any pending feedback from thumbs up/down
# that wasn't acknowledged in previous sessions.
#
# Created: Dec 29, 2025
# Purpose: Ensure no feedback is lost between sessions
#

set -euo pipefail

FEEDBACK_DIR="$CLAUDE_PROJECT_DIR/data/feedback"
PENDING_FILE="$FEEDBACK_DIR/pending.json"

# Check if there's pending feedback
if [[ ! -f "$PENDING_FILE" ]]; then
    # No pending feedback - that's fine
    exit 0
fi

# Check if file is empty or has no entries
PENDING_COUNT=$(jq -r 'length // 0' "$PENDING_FILE" 2>/dev/null || echo "0")

if [[ "$PENDING_COUNT" -eq 0 ]]; then
    exit 0
fi

# Alert about pending feedback
echo "════════════════════════════════════════════════════════════"
echo "📊 PENDING FEEDBACK DETECTED"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "You have $PENDING_COUNT unprocessed feedback items."
echo "Run '/reflect' to process and learn from this feedback."
echo ""
echo "════════════════════════════════════════════════════════════"

exit 0
