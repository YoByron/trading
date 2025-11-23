#!/bin/bash
# Full workflow test with ACT (runs actual workflow steps)
# Use this for comprehensive testing before major changes

set -e

WORKFLOW_NAME="${1:-daily-trading.yml}"

if [ -z "$1" ]; then
    echo "Usage: $0 <workflow-file>"
    echo ""
    echo "Example:"
    echo "  $0 .github/workflows/daily-trading.yml"
    echo ""
    echo "Available workflows:"
    ls -1 .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null | grep -v ".disabled" || true
    exit 1
fi

if [ ! -f "$WORKFLOW_NAME" ]; then
    echo "❌ Workflow file not found: $WORKFLOW_NAME"
    exit 1
fi

echo "🧪 Running full ACT test for: $WORKFLOW_NAME"
echo ""

# Check for secrets file
if [ -f ".secrets" ]; then
    echo "📝 Loading secrets from .secrets file"
    SECRETS_FLAG="--secret-file .secrets"
else
    echo "⚠️  No .secrets file found. Some steps may fail without secrets."
    echo "   Create .secrets file with format: SECRET_NAME=value"
    SECRETS_FLAG=""
fi

# Run ACT with workflow_dispatch event
act workflow_dispatch \
    --workflows "$WORKFLOW_NAME" \
    $SECRETS_FLAG \
    --env-file .env 2>&1 | tee /tmp/act-test.log

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if grep -q "Error" /tmp/act-test.log; then
    echo "❌ Workflow test failed!"
    exit 1
else
    echo "✅ Workflow test completed!"
fi

