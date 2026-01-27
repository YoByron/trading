#!/bin/bash
#
# Semantic RAG Context Hook - Query LanceDB on every user prompt
#
# Injects relevant lessons from RAG based on user's message
# This ensures Claude always has context before responding
#

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
SEMANTIC_MEMORY="$SCRIPT_DIR/../scripts/feedback/semantic-memory-v2.py"
VENV_PYTHON="$SCRIPT_DIR/../../.venv/bin/python3"

# Read user message from stdin
USER_MESSAGE=$(cat)

# Only query if we have semantic memory and message is substantial
if [[ -f "$SEMANTIC_MEMORY" ]] && [[ ${#USER_MESSAGE} -gt 10 ]]; then
    # Query LanceDB for relevant context (top 3 lessons)
    CONTEXT=$($VENV_PYTHON "$SEMANTIC_MEMORY" --query "$USER_MESSAGE" -n 3 2>/dev/null || echo "")

    if [[ -n "$CONTEXT" && "$CONTEXT" != *"No results"* ]]; then
        echo "═══════════════════════════════════════════════════════════"
        echo "📚 RAG CONTEXT (Semantic Search)"
        echo "═══════════════════════════════════════════════════════════"
        echo "$CONTEXT" | head -30
        echo "═══════════════════════════════════════════════════════════"
    fi
fi

# Pass through the original message
echo "$USER_MESSAGE"
