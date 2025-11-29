#!/bin/bash
# Pre-commit hook to verify crypto trading imports work without RAG

set -e

echo "🔍 Testing crypto trading imports (pre-commit check)..."

# Test that autonomous_trader can be imported
python3 -c "
import sys
import scripts.autonomous_trader
print('✅ autonomous_trader imports OK')

# Verify sentiment_store was NOT imported
if 'src.rag.sentiment_store' in sys.modules:
    print('❌ ERROR: sentiment_store was imported (should be lazy)')
    sys.exit(1)
else:
    print('✅ sentiment_store NOT imported (lazy loading works)')
"

echo "✅ Crypto trading import check passed"

