# LanceDB Migration - Quick Start

## TL;DR

```bash
# Install dependencies
pip install -r requirements-rag.txt

# Run migration (automated test suite)
bash scripts/test_lancedb_migration.sh
```

Done! ✅

---

## Manual Step-by-Step

### 1. Install Dependencies

```bash
pip install lancedb fastembed pyarrow tqdm chromadb
```

### 2. Preview Migration (Dry Run)

```bash
python scripts/migrate_to_lancedb.py --dry-run
```

**Output:**
- ChromaDB docs found: 141
- JSON docs found: 1113
- Total before dedup: 1254
- Duplicates removed: ~X
- Final unique docs: ~Y

### 3. Run Migration

```bash
# Migrate from both sources (recommended)
python scripts/migrate_to_lancedb.py --source all

# OR migrate from specific source
python scripts/migrate_to_lancedb.py --source chromadb  # ChromaDB only
python scripts/migrate_to_lancedb.py --source json      # JSON only
```

**Progress bars:**
- ✓ Reading from ChromaDB
- ✓ Reading from JSON
- ✓ Deduplicating documents
- ✓ Embedding documents (batch size: 256)
- ✓ Writing to LanceDB
- ✓ Creating vector index

### 4. Verify Migration

```bash
python scripts/verify_lancedb_migration.py
```

**Checks:**
- ✅ Document count
- ✅ Schema structure
- ✅ Embedding dimensions (384)
- ✅ Vector search functionality
- ✅ Metadata filtering
- ✅ Summary statistics

---

## CLI Options

### migrate_to_lancedb.py

```bash
--source {chromadb,json,all}  # Source to migrate from (default: all)
--chromadb-path PATH           # Path to ChromaDB (default: data/rag/chroma_db)
--json-path PATH               # Path to JSON store (default: data/rag/in_memory_store.json)
--lancedb-path PATH            # Path to LanceDB (default: data/rag/lance_db)
--model NAME                   # FastEmbed model (default: BAAI/bge-small-en-v1.5)
--dry-run                      # Preview without writing
```

### Examples

```bash
# Custom paths
python scripts/migrate_to_lancedb.py \
  --chromadb-path /custom/chromadb \
  --lancedb-path /custom/lancedb

# Different embedding model
python scripts/migrate_to_lancedb.py \
  --model sentence-transformers/all-MiniLM-L6-v2

# JSON only with dry run
python scripts/migrate_to_lancedb.py \
  --source json \
  --dry-run
```

---

## What Gets Migrated

### Data Sources

| Source | Location | Documents | Duplicates |
|--------|----------|-----------|------------|
| ChromaDB | `data/rag/chroma_db/` | 141 | Some |
| JSON Store | `data/rag/in_memory_store.json` | 1113 | Many |
| **Combined** | **After dedup** | **~1000+** | **Removed** |

### Metadata Preserved

All metadata fields are migrated:

- ✅ `ticker` - Stock ticker symbol (NVDA, TSLA, etc.)
- ✅ `source` - Original source (yahoo, bloomberg, etc.)
- ✅ `date` - Document date (YYYY-MM-DD)
- ✅ `url` - Source URL
- ✅ `sentiment` - Sentiment analysis result

Plus migration metadata:

- ✅ `migrated_from` - Source system (chromadb/json)
- ✅ `migrated_at` - Migration timestamp (ISO format)

### Embeddings

All documents are **re-embedded** using:

- **Model**: BAAI/bge-small-en-v1.5 (via FastEmbed)
- **Dimension**: 384
- **Speed**: ~1000 docs/second (CPU)
- **Quality**: State-of-the-art semantic search

---

## Expected Output

### Migration Statistics

```
====================================================================
MIGRATION STATISTICS
====================================================================
ChromaDB documents read:      141
JSON documents read:          1,113
Total before deduplication:   1,254
Duplicates removed:           X
Final unique documents:       Y
Errors encountered:           0
====================================================================
Deduplication rate:           X.X%
====================================================================
```

### Verification Results

```
====================================================================
LANCEDB VERIFICATION SUMMARY
====================================================================
Total documents:              1,XXX
Unique tickers:               XX
Date range:                   2025-XX-XX to 2025-XX-XX
Sources:                      chromadb, json

Top 5 tickers by document count:
  NVDA: XXX
  TSLA: XXX
  GOOGL: XXX
  AMZN: XXX
  MSFT: XXX
====================================================================
```

---

## Troubleshooting

### ❌ ImportError: No module named 'lancedb'

**Solution:**
```bash
pip install lancedb fastembed pyarrow tqdm chromadb
```

### ❌ Out of Memory during embedding

**Solution:**
Edit `scripts/migrate_to_lancedb.py`, reduce batch size:

```python
batch_size = 128  # Change from 256 to 128
```

### ❌ Migration takes too long

**Expected times:**
- 100 docs: ~10 seconds
- 1000 docs: ~60 seconds
- 10000 docs: ~10 minutes

**To speed up:**
- Use GPU (FastEmbed supports CUDA)
- Increase batch size (if memory allows)

### ❌ Verification fails

**Solution:**
```bash
# Re-run migration with dry-run to check data
python scripts/migrate_to_lancedb.py --dry-run

# Check logs for errors
# Ensure all dependencies installed
pip install -r requirements-rag.txt

# Check disk space
df -h
```

---

## Post-Migration

After successful migration:

1. ✅ **Keep old data** - ChromaDB and JSON are NOT deleted (safe rollback)
2. ✅ **Test searches** - Verify vector search works as expected
3. ✅ **Update code** - Modify RAG code to use LanceDB
4. ✅ **Monitor performance** - Compare speed vs ChromaDB
5. ✅ **Archive old data** - After 30-day validation period

### Quick Test Search

```python
import lancedb

db = lancedb.connect("data/rag/lance_db")
table = db.open_table("market_news")

# Search for NVIDIA earnings
results = table.search("NVIDIA earnings growth").limit(5).to_pandas()
print(results[["ticker", "document", "date"]])
```

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/migrate_to_lancedb.py` | Main migration script |
| `scripts/verify_lancedb_migration.py` | Verification script |
| `scripts/test_lancedb_migration.sh` | Automated test suite |
| `docs/lancedb_migration.md` | Full documentation |
| `data/rag/lance_db/` | LanceDB storage (created) |

---

## Support

- 📖 **Full docs**: `docs/lancedb_migration.md`
- 🐛 **Issues**: Check logs in migration output
- 💬 **Questions**: Review troubleshooting section above

---

**Last Updated**: 2025-12-12
