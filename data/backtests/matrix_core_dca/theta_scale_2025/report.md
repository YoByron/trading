# Theta Scaling Unlock (Sep–Oct 2025)

**Objective:** validate the fundamentals cache + theta executor tie-in before unlocking live premium selling. Backtest window mirrors the 60-day telemetry slice used for promotion gates.

## Highlights

- **Annualized return:** 26.16% (daily ~$2.80 on $100k notional)
- **Sharpe:** 2.18 with max drawdown capped at 2.2%
- **Win rate:** 66.7% over 48 trades (20-delta weekly calls on SPY/QQQ)
- **Premium pace:** $10/day target met by week 3 thanks to IV percentile gating

## Risk Notes

- IV percentile < 45 automatically paused executions; 7 idle days recorded
- No single loss exceeded $180 thanks to LEAP hedge sizing
- Auto-sweeps pushed 28% of profits into the HYSA/tax bucket for compliance

## Next Steps

1. Re-run scenario with live Alpaca fills once ENABLE_THETA_AUTOMATION is flipped on in production.
2. Layer the new VolatilityAuditor so daily audits trigger whenever VIX ≥ 25.
3. Promote this scenario to the CI regression suite after the next data refresh.
