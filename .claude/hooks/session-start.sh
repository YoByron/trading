#!/usr/bin/env bash
# Session Start Hook - compact trading context plus shared ThumbGate summary.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

echo "============================================"
echo "SESSION START - Trading System"
echo "============================================"
echo ""
echo "Trading Context:"
echo "  Strategy: Iron Condors on SPY (15-20 delta)"
echo '  Capital: $100,000 paper (PA3C5AG0CECQ)'
echo '  Position limit: 5% max ($5,000 risk per trade)'
echo "  Exit: 50% profit OR 7 DTE | Stop: 100% of credit"
echo ""
echo "Mandatory Rules:"
echo "  1. Phil Town Rule #1: Don't lose money"
echo "  2. Thumbs down -> record the failure pattern before continuing"
echo "  3. Use ThumbGate as the canonical local feedback path"
echo ""

python3 "${PROJECT_ROOT}/scripts/thumbgate_session_start.py" || true
echo ""
