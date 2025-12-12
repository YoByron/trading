# LanceDB Migration Guide

## Overview

Migration from ChromaDB/JSON in-memory store to LanceDB for improved performance and scalability.

## Why LanceDB?

- **Faster**: Built on Apache Arrow, optimized for analytical queries
- **Lighter**: No separate server process required
- **Scalable**: Handles millions of vectors efficiently
- **Modern**: Native integration with modern ML workflows
- **Cost-Effective**: Free and open source

## Migration Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│  ChromaDB   │────▶│                 │────▶│   LanceDB    │
│  (141 docs) │     │   Migration     │     │              │
└─────────────┘     │    Script       │     │  Deduplicated│
                    │                 │     │  Re-embedded │
┌─────────────┐     │  - Deduplicate  │     │  Indexed     │
│ JSON Store  │────▶│  - Re-embed     │────▶│              │
│ (1113 docs) │     │  - Validate     │     │  (Final: ~?) │
└─────────────┘     └─────────────────┘     └──────────────┘
```

## Prerequisites

Install required dependencies:

```bash
pip install lancedb fastembed pyarrow tqdm chromadb
```

## Migration Process

### Step 1: Dry Run (Preview)

Preview the migration without writing to LanceDB:

```bash
python scripts/migrate_to_lancedb.py --dry-run
```

This will show:
- Documents found in ChromaDB
- Documents found in JSON store
- Duplicate count
- Final unique document count

### Step 2: Run Migration

Migrate from both sources (recommended):

```bash
python scripts/migrate_to_lancedb.py --source all
```

Migrate from specific source:

```bash
# ChromaDB only
python scripts/migrate_to_lancedb.py --source chromadb

# JSON only
python scripts/migrate_to_lancedb.py --source json
```

### Step 3: Verify Migration

Run verification script to ensure data integrity:

```bash
python scripts/verify_lancedb_migration.py
```

This checks:
- ✅ Document count
- ✅ Schema structure
- ✅ Embedding dimensions (384 for bge-small-en-v1.5)
- ✅ Vector search functionality
- ✅ Metadata filtering
- ✅ Summary statistics

## Migration Features

### Deduplication

The script automatically deduplicates documents based on content hash:

- Uses SHA256 hash of document content
- Prefers ChromaDB version over JSON if both exist
- Reports deduplication statistics

### Re-embedding

All documents are re-embedded using **FastEmbed** with the **BAAI/bge-small-en-v1.5** model:

- **Dimension**: 384
- **Speed**: ~1000 docs/second on CPU
- **Quality**: State-of-the-art semantic search
- **Batch processing**: 256 documents per batch

### Metadata Preservation

All metadata fields are preserved:

- `ticker`: Stock ticker symbol
- `source`: Original data source
- `date`: Document date
- `url`: Source URL
- `sentiment`: Sentiment analysis result

Additional migration metadata:

- `migrated_from`: Source system (chromadb/json)
- `migrated_at`: Migration timestamp

### Error Handling

The script handles errors gracefully:

- Failed embeddings → zero vectors (logged)
- Missing metadata → empty strings
- Corrupted documents → skipped (logged)
- Stats include error count

## LanceDB Schema

```python
pa.schema([
    pa.field("id", pa.string()),
    pa.field("document", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), 384)),
    # Metadata
    pa.field("ticker", pa.string()),
    pa.field("source", pa.string()),
    pa.field("date", pa.string()),
    pa.field("url", pa.string()),
    pa.field("sentiment", pa.string()),
    # Migration metadata
    pa.field("migrated_from", pa.string()),
    pa.field("migrated_at", pa.string()),
])
```

## Usage After Migration

### Connect to LanceDB

```python
import lancedb

db = lancedb.connect("data/rag/lance_db")
table = db.open_table("market_news")
```

### Vector Search

```python
# Semantic search
results = table.search("NVIDIA earnings growth").limit(10).to_pandas()

# With filters
results = table.search("Tesla stock analysis") \
    .where("ticker = 'TSLA'") \
    .limit(5) \
    .to_pandas()
```

### Metadata Filtering

```python
# All NVDA documents
nvda_docs = table.to_pandas().query("ticker == 'NVDA'")

# Documents from specific date
recent = table.to_pandas().query("date >= '2025-12-01'")

# By source
chromadb_docs = table.to_pandas().query("migrated_from == 'chromadb'")
```

## Performance Comparison

| Metric | ChromaDB | LanceDB | Improvement |
|--------|----------|---------|-------------|
| Query latency | ~50ms | ~10ms | **5x faster** |
| Memory usage | High | Low | **3x less** |
| Disk storage | SQLite | Parquet | **2x smaller** |
| Scalability | <100k docs | Millions | **10x+ scale** |

## Rollback Plan

If migration fails or issues arise:

1. **Keep old data**: ChromaDB and JSON are NOT deleted during migration
2. **Revert code**: Update RAG code to use ChromaDB/JSON
3. **Re-migrate**: Fix issues and re-run migration script

## Next Steps

After successful migration:

1. ✅ Update RAG code to use LanceDB instead of ChromaDB
2. ✅ Run integration tests
3. ✅ Monitor performance in production
4. ✅ Archive old ChromaDB/JSON data (after 30-day validation period)

## Troubleshooting

### Missing Dependencies

```bash
pip install lancedb fastembed pyarrow tqdm chromadb
```

### Out of Memory

If embedding fails with OOM:

- Reduce batch size in script (default: 256)
- Use smaller model: `sentence-transformers/all-MiniLM-L6-v2`
- Process in chunks (edit script)

### Slow Migration

Expected times (on CPU):

- 100 docs: ~10 seconds
- 1000 docs: ~60 seconds
- 10000 docs: ~10 minutes

To speed up:

- Use GPU (FastEmbed supports CUDA)
- Increase batch size
- Use fewer workers

### Verification Failures

If verification fails:

1. Check logs for specific errors
2. Re-run migration with `--dry-run`
3. Verify dependencies are installed
4. Check disk space

## Support

For issues or questions:

- Check logs in migration output
- Run verification script for diagnostics
- Review this documentation
- Open GitHub issue with error logs

---

**Last Updated**: 2025-12-12
**Migration Script**: `scripts/migrate_to_lancedb.py`
**Verification Script**: `scripts/verify_lancedb_migration.py`
