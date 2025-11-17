#!/bin/bash
# CoinSnacks Newsletter Signal Fetcher
# This script is run by Claude Code via MCP to fetch CoinSnacks signals
# Claude fetches via MCP RSS tool, analyzes content, writes to JSON
#
# Usage:
#   ./scripts/fetch_newsletter_signals.sh
#
# Expected MCP Tool Usage by Claude:
#   1. Use MCP RSS tool to fetch CoinSnacks feed (https://coinsnacks.com/feed/)
#   2. Parse latest article content for BTC/ETH signals
#   3. Extract: sentiment, recommended coin, reasoning, confidence
#   4. Write structured JSON to data/newsletter_signals_YYYY-MM-DD.json
#
# This script creates a template that Claude will populate

set -e

# Configuration
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
OUTPUT_FILE="data/newsletter_signals_${DATE}.json"

# Ensure data directory exists
mkdir -p data

# Create template JSON (Claude Code will populate this)
cat > "$OUTPUT_FILE" << EOF
{
  "date": "${DATE}",
  "source": "CoinSnacks",
  "btc_signal": "neutral",
  "eth_signal": "neutral",
  "recommended_coin": "NONE",
  "reasoning": "Newsletter not yet fetched - template created",
  "confidence": 0.0,
  "fetched_at": "${TIMESTAMP}",
  "newsletter_url": "https://coinsnacks.com/",
  "status": "pending_fetch"
}
EOF

echo "✅ Created template at $OUTPUT_FILE"
echo ""
echo "📋 Next Steps (Claude Code will do this):"
echo "  1. Use MCP RSS tool to fetch https://coinsnacks.com/feed/"
echo "  2. Analyze latest CoinSnacks article content"
echo "  3. Extract BTC/ETH signals (bullish/bearish/neutral)"
echo "  4. Identify recommended coin with confidence score"
echo "  5. Update $OUTPUT_FILE with actual signals"
echo ""
echo "⏰ Schedule: Every Sunday at 8:00 AM (before 10:00 AM crypto trades)"
echo ""
echo "🔧 Manual Override: Claude Code can be asked to fetch anytime"
