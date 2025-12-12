#!/usr/bin/env python3
"""
LanceDB Search Testing Script

Quick tests for LanceDB vector search after migration.

Usage:
    python scripts/test_lancedb_search.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import lancedb
    import pandas as pd
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install lancedb pandas")
    sys.exit(1)


def main():
    """Run test searches against LanceDB."""
    print("=" * 60)
    print("LanceDB Search Testing")
    print("=" * 60)
    print()

    # Connect to LanceDB
    lancedb_path = "data/rag/lance_db"
    print(f"Connecting to LanceDB: {lancedb_path}")

    try:
        db = lancedb.connect(lancedb_path)
        table = db.open_table("market_news")
        print(f"✅ Connected to LanceDB ({table.count_rows():,} documents)")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    print()

    # Test queries
    test_queries = [
        {
            "query": "NVIDIA earnings and revenue growth",
            "ticker": "NVDA",
            "description": "NVIDIA earnings search with ticker filter",
        },
        {
            "query": "Tesla stock performance and deliveries",
            "ticker": "TSLA",
            "description": "Tesla stock analysis",
        },
        {
            "query": "S&P 500 market trends and analysis",
            "ticker": None,
            "description": "General market analysis (no ticker filter)",
        },
        {
            "query": "AI and machine learning investment opportunities",
            "ticker": None,
            "description": "Semantic search for AI-related content",
        },
    ]

    for i, test in enumerate(test_queries, 1):
        print(f"Test {i}: {test['description']}")
        print(f"Query: '{test['query']}'")

        if test["ticker"]:
            print(f"Filter: ticker = {test['ticker']}")

        try:
            # Perform search
            query = table.search(test["query"]).limit(5)

            # Add filter if ticker specified
            if test["ticker"]:
                query = query.where(f"ticker = '{test['ticker']}'")

            # Execute query
            results = query.to_pandas()

            if len(results) == 0:
                print("  ⚠️  No results found")
            else:
                print(f"  ✅ Found {len(results)} results")
                print()

                # Display results
                for idx, row in results.iterrows():
                    print(f"  [{idx + 1}] Ticker: {row['ticker'] or 'N/A'}")
                    print(f"      Date: {row['date'] or 'N/A'}")
                    print(f"      Document: {row['document'][:150]}...")
                    print(f"      Source: {row['migrated_from']}")
                    print()

        except Exception as e:
            print(f"  ❌ Search failed: {e}")

        print("-" * 60)
        print()

    # Summary statistics
    print("=" * 60)
    print("Database Statistics")
    print("=" * 60)

    try:
        df = table.to_pandas()

        print(f"Total documents:       {len(df):,}")
        print(f"Unique tickers:        {df['ticker'].nunique()}")
        print(f"Date range:            {df['date'].min()} to {df['date'].max()}")
        print()

        print("Top 10 tickers by document count:")
        ticker_counts = df["ticker"].value_counts().head(10)
        for ticker, count in ticker_counts.items():
            if ticker:
                print(f"  {ticker:8s} {count:4d} documents")

        print()
        print("Documents by source:")
        source_counts = df["migrated_from"].value_counts()
        for source, count in source_counts.items():
            print(f"  {source:10s} {count:4d} documents")

    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")

    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
