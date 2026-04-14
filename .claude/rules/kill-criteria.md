# Kill Criteria — IC Simple Validation

## Status — ACTIVE as of April 14, 2026

## Hypothesis

With execution fixes applied (hold period, position limits, single exit system,
regime gate, delta verification), the 15-delta SPY iron condor strategy will
produce positive expectancy over 30 clean trades.

## Kill Conditions (ANY triggers removal)

1. **Expectancy ≤ 0** after 30 closed validation trades
2. **Profit factor ≤ 1.0** after 30 closed validation trades
3. **Win rate below break-even level** (given realized avg win/loss ratio)
4. **3 consecutive max-loss stops** in the validation cohort
5. **Account drawdown exceeds 10%** from validation start ($93,723 → below $84,351)

## If killed

- IC Simple is removed as a North Star candidate
- Strategy redesign required with a new written hypothesis
- No "just keep trading" — a specific changed rule must be tested

## Audit of failed 67 trades (evidence)

- 79% held < 4 hours (no theta decay)
- 35 trades on single expiry (concentrated risk)
- 100% exit reasons "unknown" (no learning)
- Avg win $70.50, avg loss -$95.94 (inverted risk/reward)
- Total P/L: -$3,669

## What the fixes changed

- 24h minimum hold (was: hours)
- 1 trade/day max (was: 82/day)
- Same-expiry re-entry blocked (was: unlimited)
- Exit reasons recorded (was: unknown)
- Single exit system (was: 2 competing)
