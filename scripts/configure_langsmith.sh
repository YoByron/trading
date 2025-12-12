#!/bin/bash
# Configure Langsmith for trading system
# This script will be automatically run after you get your API key

set -e

echo "🔍 Langsmith Configuration Setup"
echo "================================"
echo ""

# Check if API key is already in .env
if grep -q "LANGSMITH_API_KEY" .env 2>/dev/null; then
    echo "✅ LANGSMITH_API_KEY already configured in .env"
else
    echo "⚠️  Please add your Langsmith API key to .env:"
    echo ""
    echo "LANGSMITH_API_KEY=your_api_key_here"
    echo "LANGSMITH_PROJECT=igor-trading-system"
    echo "LANGSMITH_ENDPOINT=https://api.smith.langchain.com"
    echo "LANGSMITH_TRACING=true"
    echo ""
fi

# Verify the configuration
if [ -f .env ]; then
    source .env
    if [ -n "$LANGSMITH_API_KEY" ] && [ "$LANGSMITH_API_KEY" != "your_api_key_here" ]; then
        echo "✅ Langsmith configuration valid"
        echo "📊 Dashboard: https://smith.langchain.com/o/igor-ganapolsky/projects/p/igor-trading-system"
    else
        echo "⚠️  Please update LANGSMITH_API_KEY in .env with your actual API key"
    fi
else
    echo "❌ .env file not found"
    exit 1
fi
