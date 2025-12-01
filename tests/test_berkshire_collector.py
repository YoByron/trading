#!/usr/bin/env python3
"""
Test script for Berkshire Hathaway shareholder letters collector.

This script demonstrates the collector's capabilities:
1. Download all shareholder letters (1977-2024)
2. Search for investment wisdom
3. Extract stock mentions
4. Demonstrate RAG search
"""

import logging
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag.collectors.berkshire_collector import BerkshireLettersCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """Test the Berkshire letters collector."""
    print("=" * 80)
    print("BERKSHIRE HATHAWAY SHAREHOLDER LETTERS COLLECTOR - TEST")
    print("=" * 80)
    print()

    # Initialize collector
    print("Initializing collector...")
    collector = BerkshireLettersCollector()
    print(f"✓ Collector initialized (cache: {collector.cache_dir})")
    print()

    # Check if letters are already cached
    if len(collector.index) > 0:
        print(f"✓ Found {len(collector.index)} cached letters")
        print(f"  Years: {sorted(collector.index.keys())}")
    else:
        print("No cached letters found - downloading...")
        count = collector.download_all_letters()
        print(f"✓ Downloaded {count} letters")
    print()

    # Test 1: Search for investment wisdom
    print("-" * 80)
    print("TEST 1: Search for 'index funds vs stock picking'")
    print("-" * 80)
    results = collector.search("index funds vs stock picking", top_k=3)
    print(f"Query: {results['query']}")
    print(f"Years referenced: {results['years_referenced']}")
    print(f"Buffett's view: {results['sentiment'][:200]}...")
    print()
    print("Top excerpts:")
    for i, excerpt in enumerate(results["relevant_excerpts"][:2], 1):
        print(f"\n  {i}. Year {excerpt['year']} ({excerpt['url']}):")
        for j, text in enumerate(excerpt["excerpts"][:2], 1):
            print(f"     {j}. {text[:150]}...")
    print()

    # Test 2: Search for specific topic
    print("-" * 80)
    print("TEST 2: Search for 'intrinsic value'")
    print("-" * 80)
    results = collector.search("intrinsic value calculating business worth", top_k=3)
    print(f"Query: {results['query']}")
    print(f"Years referenced: {results['years_referenced']}")
    print(f"Number of relevant excerpts: {len(results['relevant_excerpts'])}")
    if results["relevant_excerpts"]:
        print(f"\nMost relevant year: {results['relevant_excerpts'][0]['year']}")
        print(f"Excerpt: {results['relevant_excerpts'][0]['excerpts'][0][:200]}...")
    print()

    # Test 3: Stock mentions
    print("-" * 80)
    print("TEST 3: Apple (AAPL) mentions across all letters")
    print("-" * 80)
    aapl_mentions = collector.get_stock_mentions("AAPL")
    if aapl_mentions:
        print(f"Found {len(aapl_mentions)} years mentioning Apple:")
        for mention in aapl_mentions:
            print(
                f"  • {mention['year']}: {mention['mention_count']} mentions "
                f"(sentiment: {mention['sentiment']})"
            )
    else:
        print("No Apple mentions found (may need to update KNOWN_TICKERS)")
    print()

    # Test 4: Coca-Cola mentions (classic Buffett holding)
    print("-" * 80)
    print("TEST 4: Coca-Cola (KO) mentions across all letters")
    print("-" * 80)
    ko_mentions = collector.get_stock_mentions("KO")
    if ko_mentions:
        print(f"Found {len(ko_mentions)} years mentioning Coca-Cola:")
        for mention in ko_mentions[:5]:  # First 5
            print(
                f"  • {mention['year']}: {mention['mention_count']} mentions "
                f"(sentiment: {mention['sentiment']})"
            )
        if len(ko_mentions) > 5:
            print(f"  ... and {len(ko_mentions) - 5} more years")
    else:
        print("No Coca-Cola mentions found")
    print()

    # Test 5: Get a specific letter
    print("-" * 80)
    print("TEST 5: Retrieve full 2023 letter")
    print("-" * 80)
    letter_2023 = collector.get_letter(2023)
    if letter_2023:
        print(f"✓ Retrieved 2023 letter ({len(letter_2023)} characters)")
        print("First 300 characters:")
        print(f"  {letter_2023[:300]}...")
    else:
        print("2023 letter not available")
    print()

    # Test 6: Collect ticker news (BaseNewsCollector interface)
    print("-" * 80)
    print("TEST 6: Collect ticker news for American Express (AXP)")
    print("-" * 80)
    axp_articles = collector.collect_ticker_news("AXP")
    if axp_articles:
        print(f"Found {len(axp_articles)} articles (letter excerpts) mentioning AXP:")
        for article in axp_articles[:3]:
            print(f"\n  • {article['title']}")
            print(f"    Published: {article['published_date']}")
            print(f"    Sentiment: {article.get('sentiment', 'N/A')}")
            print(f"    Content preview: {article['content'][:150]}...")
    else:
        print("No AXP mentions found")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total letters cached: {len(collector.index)}")
    print(f"Cache location: {collector.cache_dir}")
    print(f"Index file: {collector.index_file}")
    print()
    print("✓ All tests completed successfully!")
    print()
    print("You can now use this collector for:")
    print("  • Semantic search: collector.search('your query')")
    print("  • Stock mentions: collector.get_stock_mentions('TICKER')")
    print("  • Full letters: collector.get_letter(year)")
    print("  • RAG integration: Use with LangChain/LlamaIndex for Q&A")
    print()


if __name__ == "__main__":
    main()
