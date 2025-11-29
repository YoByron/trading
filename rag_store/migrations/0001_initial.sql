BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sentiment_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    ticker TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    score REAL NOT NULL,
    confidence TEXT NOT NULL,
    market_regime TEXT,
    summary TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(source, ticker, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_ticker_date
    ON sentiment_snapshots (ticker, snapshot_date);

COMMIT;
