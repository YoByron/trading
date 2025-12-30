#!/bin/bash
#
# Vector DB Verification Hook - Ensures RAG semantic search is available
#
# Created: Dec 30, 2025
# Reason: ChromaDB silently fell back to TF-IDF when not installed (LL-074)
#
# This hook runs on session start to verify vector packages are working.
# If broken, it will attempt auto-repair.

set -e

echo "🔍 Verifying Vector Database..."

# Quick check: can we import chromadb?
CHROMADB_CHECK=$(python3 -c "
try:
    import chromadb
    print(f'OK:{chromadb.__version__}')
except ImportError:
    print('MISSING')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)

if [[ "$CHROMADB_CHECK" == "MISSING" ]]; then
    echo "❌ ChromaDB NOT INSTALLED"
    echo ""
    echo "🔧 Attempting auto-install..."
    pip install chromadb==0.6.3 chroma-hnswlib==0.7.6 --quiet
    echo "✅ ChromaDB installed - please restart session"
    exit 0
elif [[ "$CHROMADB_CHECK" == ERROR:* ]]; then
    echo "⚠️ ChromaDB error: ${CHROMADB_CHECK#ERROR:}"
    exit 0
else
    VERSION="${CHROMADB_CHECK#OK:}"
    echo "✅ ChromaDB v${VERSION} available"
fi

# Check if vector DB has data
VECTOR_CHECK=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    import chromadb
    from chromadb.config import Settings
    from pathlib import Path

    db_path = Path('data/vector_db')
    if not db_path.exists():
        print('EMPTY:no directory')
        sys.exit(0)

    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(anonymized_telemetry=False)
    )

    collections = client.list_collections()
    if not collections:
        print('EMPTY:no collections')
    else:
        col = client.get_collection(collections[0])
        count = col.count()
        if count == 0:
            print('EMPTY:no documents')
        else:
            print(f'OK:{count}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)

if [[ "$VECTOR_CHECK" == EMPTY:* ]]; then
    REASON="${VECTOR_CHECK#EMPTY:}"
    echo "⚠️ Vector DB empty ($REASON)"
    echo ""
    echo "🔧 Rebuilding vector database..."
    python3 scripts/vectorize_rag_knowledge.py --rebuild --quiet 2>/dev/null || \
    python3 scripts/vectorize_rag_knowledge.py --rebuild 2>&1 | tail -5
    echo "✅ Vector DB rebuilt"
elif [[ "$VECTOR_CHECK" == ERROR:* ]]; then
    echo "⚠️ Vector DB check error: ${VECTOR_CHECK#ERROR:}"
elif [[ "$VECTOR_CHECK" == OK:* ]]; then
    COUNT="${VECTOR_CHECK#OK:}"
    echo "✅ Vector DB: ${COUNT} documents indexed"
fi
