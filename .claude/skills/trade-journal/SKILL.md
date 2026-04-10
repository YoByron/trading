---
name: trade-journal
description: Audit trail for every trade in the controlled experiment (30-trade validation)
version: 1.0.0
context: fork
triggers:
  - trade-journal
---

# Trade Journal Skill

Produces a structured audit record for every iron condor trade, per the controlled experiment protocol.

## Trigger

- `/trade-journal` - Show current journal with all validation trades

## What It Does

1. Reads `data/ic_entries.json` for open positions with `validation_phase: true`
2. Reads `data/trades.json` for closed validation trades
3. For each trade, reports: actual short deltas, DTE at entry, selection method, hold time, exit reason, expiry cluster, P/L
4. Flags any protocol violations (parameter drift, same-expiry re-entry after loss, hold < 24h)

## Instructions

When triggered, run:

```bash
PYTHONPATH=. python3 scripts/trade_journal.py
```

If the script doesn't exist yet, read `data/ic_entries.json` and `data/trades.json` directly and format the audit table.

Show results as a markdown table with columns: #, Entry Date, Expiry, Short Strikes, Deltas, Credit, DTE, Method, Status, Hold Time, Exit Reason, P/L.
