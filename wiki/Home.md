# SPY Options Validation Platform Wiki

Generated from canonical ledgers at `2026-05-18T17:14:20.572173+00:00`.

This wiki is generated from the same source used by the public dashboard and repo copy. It should never carry frozen win-rate, equity, or trade-count claims that drift from the ledgers.

## Current Snapshot

- Public status: `validation_reset`
- Paper equity: `$94,609.31`
- Closed trades total: `69`
- Total realized P/L: `$-3,958.00`
- Weekly gate mode: `validation_reset`

## Key Links

- [Public dashboard](https://igorganapolsky.github.io/trading)
- [Operator dashboard](https://igorganapolsky.github.io/trading/rag-query.html)
- [Progress Dashboard](Progress-Dashboard)
- [Development Engine and Evidence](Development-Engine-and-Evidence)

## Operating Truth

Currently in a High-Alpha Recovery phase. Following an audit of 69 trades, the system is now restricted to its 60% win-rate Thursday window. Operational discipline is enforced via RAG-ML feedback loops and 7 DTE gamma gates.

## Current Blocker

`Negative lifetime expectancy freezes North Star claims; only minimum-size paper validation is allowed because a valid changed-rule hypothesis is present.`
