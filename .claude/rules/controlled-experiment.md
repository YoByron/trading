# Controlled Experiment Protocol (Apr 9, 2026)

## Status — ACTIVE, next 30 setups are an experiment, not income

## Rules

1. **Paper only.** No new capital. No live deployment.
2. **1 structure max per day.** 1-lot only.
3. **No same-expiry re-entry after a loss.**
4. **Minimum 24h hold** (enforced in ic_simple.py).
5. **One profile only** (spy-core). No parameter drift.
6. **Gate on expectancy, not just win rate:**
   - Pass only if realized expectancy > 0
   - Profit factor > 1
   - Win rate above realized break-even level
7. **Every trade auditable:** record actual short deltas, DTE, selection method, hold time, exit reason, expiry cluster.
8. **Broker sync must be fresh** — if stale, no new entries.
9. **Ignore "recover to $100K"** — process first, recovery second.

## Decision Gate

After 30 clean setups:

- System has edge → scale
- System has no edge → stop and redesign

## What NOT to do

- Add capital before edge is proven
- Switch to live
- Optimize only for "80% win rate" headline
- Claim the strategy is fixed before a fresh profitable sample exists
