#!/bin/bash
# Newsletter analyzer test runner
# Tests MCP integration and RSS fallback

cd "$(dirname "$0")/.." || exit 1

echo "=================================="
echo "Testing Newsletter Integration"
echo "=================================="
echo ""

# Run the test script
python3 scripts/test_newsletter_analyzer.py

echo ""
echo "=================================="
echo "Fetching Live CoinSnacks Feed"
echo "=================================="
echo ""

# Test live RSS feed
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.utils.newsletter_analyzer import NewsletterAnalyzer
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print('📡 Fetching latest CoinSnacks newsletter via RSS...\n')

analyzer = NewsletterAnalyzer()

# Try to get latest signals from RSS feed
signals = analyzer.get_latest_signals(max_age_days=7)

if signals:
    print(f'\n✅ Successfully fetched {len(signals)} crypto signals:\n')
    for ticker, signal in signals.items():
        print(f'═══ {ticker} ═══')
        print(f'Sentiment: {signal.sentiment.upper()} (confidence: {signal.confidence:.1%})')
        if signal.entry_price:
            print(f'Entry: \${signal.entry_price:,.0f}')
        if signal.target_price:
            print(f'Target: \${signal.target_price:,.0f}')
        if signal.stop_loss:
            print(f'Stop: \${signal.stop_loss:,.0f}')
        if signal.timeframe:
            print(f'Timeframe: {signal.timeframe}')
        if signal.reasoning:
            reasoning = signal.reasoning[:200] + '...' if len(signal.reasoning) > 200 else signal.reasoning
            print(f'Reasoning: {reasoning}')
        print()

    # Save signals for trading system to use
    print('💾 Saving signals for trading system...')
    saved_path = analyzer.save_signals(signals)
    print(f'✅ Saved to: {saved_path}')

else:
    print('⚠️  No crypto signals found in recent CoinSnacks articles')
    print('This may mean:')
    print('  - No recent articles mention BTC/ETH trading signals')
    print('  - RSS feed is unavailable')
    print('  - Network connectivity issue')
"
