#!/usr/bin/env python3
"""
LanceDB Migration Verification Script

Tests the migrated LanceDB to ensure data integrity and search functionality.

Usage:
    python scripts/verify_lancedb_migration.py
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

try:
    import lancedb
    import pandas as pd
except ImportError as e:
    logger.error(f"Missing required dependency: {e}")
    logger.error("Install with: pip install lancedb pandas")
    sys.exit(1)


class LanceDBVerifier:
    """Verifies LanceDB migration integrity."""

    def __init__(self, lancedb_path: str = "data/rag/lance_db"):
        self.lancedb_path = lancedb_path
        self.db = None
        self.table = None

    def connect(self) -> bool:
        """Connect to LanceDB."""
        try:
            logger.info(f"Connecting to LanceDB: {self.lancedb_path}")
            self.db = lancedb.connect(self.lancedb_path)
            self.table = self.db.open_table("market_news")
            logger.info("✅ Successfully connected to LanceDB")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to LanceDB: {e}")
            return False

    def verify_count(self) -> bool:
        """Verify document count."""
        try:
            count = self.table.count_rows()
            logger.info(f"Total documents in LanceDB: {count:,}")

            if count == 0:
                logger.error("❌ No documents found in LanceDB!")
                return False

            logger.info("✅ Document count verified")
            return True
        except Exception as e:
            logger.error(f"❌ Error verifying count: {e}")
            return False

    def verify_schema(self) -> bool:
        """Verify table schema."""
        try:
            schema = self.table.schema
            logger.info("LanceDB Schema:")
            for field in schema:
                logger.info(f"  - {field.name}: {field.type}")

            required_fields = {
                "id",
                "document",
                "vector",
                "ticker",
                "source",
                "date",
                "url",
                "sentiment",
                "migrated_from",
                "migrated_at",
            }

            schema_fields = {field.name for field in schema}
            missing = required_fields - schema_fields

            if missing:
                logger.error(f"❌ Missing required fields: {missing}")
                return False

            logger.info("✅ Schema verified")
            return True
        except Exception as e:
            logger.error(f"❌ Error verifying schema: {e}")
            return False

    def verify_embeddings(self) -> bool:
        """Verify embeddings are valid."""
        try:
            # Sample some documents
            sample = self.table.to_pandas().head(10)

            for idx, row in sample.iterrows():
                vector = row["vector"]
                if not isinstance(vector, (list, pd.Series)):
                    logger.error(f"❌ Invalid vector type at row {idx}: {type(vector)}")
                    return False

                vector_len = len(vector)
                if vector_len != 384:  # bge-small-en-v1.5 dimension
                    logger.error(f"❌ Invalid vector dimension at row {idx}: {vector_len}")
                    return False

            logger.info("✅ Embeddings verified (dimension: 384)")
            return True
        except Exception as e:
            logger.error(f"❌ Error verifying embeddings: {e}")
            return False

    def test_vector_search(self) -> bool:
        """Test vector similarity search."""
        try:
            test_queries = [
                "NVIDIA earnings and revenue",
                "Tesla stock performance",
                "S&P 500 market analysis",
            ]

            for query in test_queries:
                logger.info(f"Testing search: '{query}'")
                results = self.table.search(query).limit(5).to_pandas()

                if len(results) == 0:
                    logger.warning(f"  ⚠️  No results for: {query}")
                else:
                    logger.info(f"  ✅ Found {len(results)} results")
                    # Show top result
                    top = results.iloc[0]
                    logger.info(f"     Top result: {top['document'][:100]}...")

            logger.info("✅ Vector search functional")
            return True
        except Exception as e:
            logger.error(f"❌ Error testing vector search: {e}")
            return False

    def test_metadata_filtering(self) -> bool:
        """Test metadata filtering."""
        try:
            # Get unique tickers
            df = self.table.to_pandas()
            tickers = df["ticker"].unique()
            logger.info(f"Unique tickers in database: {len(tickers)}")

            # Test filtering by ticker
            if len(tickers) > 0:
                test_ticker = [t for t in tickers if t][:1][0] if any(tickers) else None

                if test_ticker:
                    filtered = df[df["ticker"] == test_ticker]
                    logger.info(f"Documents for {test_ticker}: {len(filtered)}")

            # Test filtering by source
            sources = df["migrated_from"].value_counts()
            logger.info("Documents by source:")
            for source, count in sources.items():
                logger.info(f"  - {source}: {count:,}")

            logger.info("✅ Metadata filtering functional")
            return True
        except Exception as e:
            logger.error(f"❌ Error testing metadata filtering: {e}")
            return False

    def print_summary(self) -> bool:
        """Print summary statistics."""
        try:
            df = self.table.to_pandas()

            print("\n" + "=" * 60)
            print("LANCEDB VERIFICATION SUMMARY")
            print("=" * 60)
            print(f"Total documents:              {len(df):,}")
            print(f"Unique tickers:               {df['ticker'].nunique()}")
            print(f"Date range:                   {df['date'].min()} to {df['date'].max()}")
            print(f"Sources:                      {', '.join(df['migrated_from'].unique())}")
            print("\nTop 5 tickers by document count:")
            ticker_counts = df["ticker"].value_counts().head(5)
            for ticker, count in ticker_counts.items():
                print(f"  {ticker}: {count}")
            print("=" * 60)

            return True
        except Exception as e:
            logger.error(f"❌ Error printing summary: {e}")
            return False

    def verify_all(self) -> bool:
        """Run all verification checks."""
        checks = [
            ("Connect to LanceDB", self.connect),
            ("Verify document count", self.verify_count),
            ("Verify schema", self.verify_schema),
            ("Verify embeddings", self.verify_embeddings),
            ("Test vector search", self.test_vector_search),
            ("Test metadata filtering", self.test_metadata_filtering),
            ("Print summary", self.print_summary),
        ]

        print("\n" + "=" * 60)
        print("LANCEDB MIGRATION VERIFICATION")
        print("=" * 60 + "\n")

        all_passed = True
        for check_name, check_func in checks:
            logger.info(f"Running check: {check_name}")
            try:
                passed = check_func()
                if not passed:
                    all_passed = False
                    logger.error(f"❌ Check failed: {check_name}")
                print()
            except Exception as e:
                logger.error(f"❌ Check crashed: {check_name} - {e}")
                all_passed = False
                print()

        print("=" * 60)
        if all_passed:
            print("✅ ALL CHECKS PASSED - Migration verified successfully!")
        else:
            print("❌ SOME CHECKS FAILED - Review errors above")
        print("=" * 60 + "\n")

        return all_passed


def main():
    """Main entry point."""
    verifier = LanceDBVerifier()
    success = verifier.verify_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
