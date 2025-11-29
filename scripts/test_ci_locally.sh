#!/bin/bash
# Test CI workflows locally using ACT

set -e

WORKFLOW="${1:-adk-ci.yml}"

echo "🧪 Testing CI workflow locally: $WORKFLOW"
echo "=========================================="

# Check if ACT is installed
if ! command -v act &> /dev/null; then
    echo "❌ ACT not installed. Run: ./scripts/setup_act.sh"
    exit 1
fi

# Check if secrets file exists
if [ ! -f .github/local-secrets.env ]; then
    echo "⚠️  .github/local-secrets.env not found"
    echo "   Creating from example..."
    cp .github/local-secrets.env.example .github/local-secrets.env
    echo "   ⚠️  Edit .github/local-secrets.env and add your API keys"
    echo "   Then run this script again"
    exit 1
fi

# Validate dependencies first
echo ""
echo "🔍 Validating dependencies..."
python3 scripts/validate_dependencies.py || {
    echo "❌ Dependency validation failed!"
    echo "   Fix issues before testing CI"
    exit 1
}

echo ""
echo "🚀 Running ACT for workflow: $WORKFLOW"
echo ""

# Run ACT with secrets
act -W ".github/workflows/$WORKFLOW" \
    --secret-file .github/local-secrets.env \
    --verbose

echo ""
echo "✅ Local CI test complete!"
