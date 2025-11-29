# Berkshire Hathaway Shareholder Letters RAG Database

This directory contains Warren Buffett's annual shareholder letters (1977-2024) parsed into a searchable knowledge base.

## Directory Structure

```
berkshire_letters/
├── raw/            # Original PDF/HTML files
├── parsed/         # Extracted text files (one per year)
├── index/          # letters_index.json (metadata and search index)
└── README.md       # This file
```

## Usage

### Using the Collector

```python
from src.rag.collectors.berkshire_collector import BerkshireLettersCollector

# Initialize
collector = BerkshireLettersCollector()

# Download all letters (first time only)
collector.download_all_letters()

# Search for investment wisdom
results = collector.search("index funds vs stock picking")
print(f"Years referenced: {results['years_referenced']}")
print(f"Buffett's view: {results['sentiment']}")

# Get all mentions of a stock
aapl_mentions = collector.get_stock_mentions("AAPL")
for mention in aapl_mentions:
    print(f"{mention['year']}: {mention['sentiment']}")

# Get full text of a specific letter
letter_2023 = collector.get_letter(2023)
```

### Search Results Format

```python
{
    "query": "index funds vs stock picking",
    "relevant_excerpts": [
        {
            "year": 2013,
            "excerpts": ["...Buffett's advice..."],
            "url": "https://..."
        }
    ],
    "years_referenced": [2013, 2016, 2020],
    "sentiment": "Buffett recommends index funds for most investors...",
    "source": "berkshire_letters"
}
```

## Features

### 1. Automatic Download and Parsing
- Downloads all letters from berkshirehathaway.com
- Parses both PDF and HTML formats
- Caches locally (letters don't change)
- Extracts metadata: stock mentions, themes, word count

### 2. Semantic Search
- Query any topic: "What does Buffett say about moats?"
- Returns relevant excerpts across all years
- Ranks by relevance score
- Cross-references multiple years

### 3. Stock Mention Tracking
- Extracts all ticker mentions (KO, AAPL, AXP, etc.)
- Sentiment analysis (bullish/bearish/neutral/mixed)
- Historical tracking across years
- Context extraction around mentions

### 4. Investment Themes
Auto-detected themes:
- `intrinsic_value` - Value investing principles
- `moat` - Competitive advantages
- `management` - Management quality
- `index_funds` - Passive investing advice
- `derivatives` - Risk warnings
- `insurance` - Float and underwriting
- `capital_allocation` - Reinvestment strategy

### 5. RAG Integration Ready
- Compatible with LangChain, LlamaIndex
- Structured JSON outputs
- Cacheable for fast retrieval
- No rate limits (local data)

## Known Stock Tickers

The collector automatically detects these companies/tickers:
- Coca-Cola (KO)
- Apple (AAPL)
- American Express (AXP)
- Bank of America (BAC)
- Wells Fargo (WFC)
- Moody's (MCO)
- Kraft Heinz (KHC)
- Chevron (CVX)
- Occidental Petroleum (OXY)
- And more...

To add more tickers, update `KNOWN_TICKERS` in `berkshire_collector.py`.

## Example Queries

```python
# Investment philosophy
results = collector.search("circle of competence")

# Risk management
results = collector.search("margin of safety")

# Business moats
results = collector.search("durable competitive advantage")

# Market timing
results = collector.search("market predictions forecasting")

# Portfolio concentration
results = collector.search("diversification")
```

## Data Freshness

Letters are published annually (typically February/March). To update:

```python
collector.download_all_letters(force_refresh=True)
```

## Integration with Trading System

This collector integrates with the trading system's RAG pipeline:

```python
from src.rag.collectors import BerkshireLettersCollector

# Use in signal analysis
collector = BerkshireLettersCollector()

# Before trading AAPL, check Buffett's view
aapl_wisdom = collector.collect_ticker_news("AAPL")
for insight in aapl_wisdom:
    print(f"{insight['title']}")
    print(f"Sentiment: {insight['sentiment']}")
    print(f"Content: {insight['content'][:200]}...")
```

## Notes

- **Website Access**: berkshirehathaway.com may block automated requests. If downloads fail, letters can be manually saved to `raw/` directory
- **PDF Parsing**: Requires `PyPDF2>=3.0.0` (included in requirements.txt)
- **Cache Size**: ~50-100MB for all letters (1977-2024)
- **Performance**: Local search is instant (<100ms)

## Future Enhancements

- [ ] Embeddings-based semantic search (vs keyword matching)
- [ ] LLM-powered summarization per year
- [ ] Cross-reference with actual stock performance
- [ ] Extract quantitative metrics (P/E ratios, returns mentioned)
- [ ] Compare Buffett's advice vs trading system performance

## License

Letters copyright Berkshire Hathaway Inc. This collector is for educational/research purposes only.
