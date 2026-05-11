# Development Engine and Evidence

Generated from canonical ledgers at `2026-05-11T19:19:35.984470+00:00`.

This page explains how public-facing system copy stays congruent with live state.

## Evidence Surfaces

- `artifacts/daily_scorecard/latest_daily_scorecard.json` for broker-backed daily status
- `data/system_state.json` for active gate state
- `data/trades.json` for paired-trade ledger stats
- `docs/data/public_status.json` for public pages and wiki rendering

## Current Public-Copy Rules

- No frozen portfolio numbers in README, About, or wiki prose
- Public pages render from generated status data or link to canonical live surfaces
- Repo metadata and wiki must match the generated public status bundle

## Current Operator Summary

- Paper equity: `$93,444.96`
- Total realized P/L ledger: `$-3,958.00`
- Weekly gate mode: `defensive`
- Block new positions: `True`

## Exact Blocker

`CRITICAL: Lifetime paired-trade ledger remains negative despite the recent weekly window. Ledger expectancy $-57.36/trade, profit factor 0.22, total realized P/L $-3958.00 over 69 closed trades. Trading halted.`
