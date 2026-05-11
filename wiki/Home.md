# SPY Options Validation Platform Wiki

Generated from canonical ledgers at `2026-05-11T17:55:36.319987+00:00`.

This wiki is generated from the same source used by the public dashboard and repo copy. It should never carry frozen win-rate, equity, or trade-count claims that drift from the ledgers.

## Current Snapshot

- Public status: `halted`
- Paper equity: `$93,473.96`
- Closed trades total: `69`
- Total realized P/L: `$-3,958.00`
- Weekly gate mode: `defensive`

## Key Links

- [Public dashboard](https://igorganapolsky.github.io/trading)
- [Operator dashboard](https://igorganapolsky.github.io/trading/rag-query.html)
- [Progress Dashboard](Progress-Dashboard)
- [Development Engine and Evidence](Development-Engine-and-Evidence)

## Operating Truth

Currently in a High-Alpha Recovery phase. Following an audit of 69 trades, the system is now restricted to its 60% win-rate Thursday window. Operational discipline is enforced via RAG-ML feedback loops and 7 DTE gamma gates.

## Current Blocker

`CRITICAL: Lifetime paired-trade ledger remains negative despite the recent weekly window. Ledger expectancy $-57.36/trade, profit factor 0.22, total realized P/L $-3958.00 over 69 closed trades. Trading halted.`
