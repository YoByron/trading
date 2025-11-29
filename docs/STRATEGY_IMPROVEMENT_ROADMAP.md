# Strategy Improvement Roadmap

**Purpose**: Actionable roadmap to fix critical strategy fundamentals and achieve profitable trading.

---

## Phase 1: Fix Automation (Week 1) - BLOCKING

### 1.1 Fix GitHub Actions Failures
**Status**: IN PROGRESS
**Action**: Fixed `Dict` import error in `technical_indicators.py`

**Next Steps**:
- [ ] Test workflow manually: `gh workflow run daily-trading.yml`
- [ ] Verify all secrets are set correctly
- [ ] Get 50+ trades executed for statistical significance

### 1.2 Fix LangSmith Initialization
**Action**: Verify `LANGCHAIN_API_KEY` is set in GitHub Secrets

---

## Phase 2: Strategy Fundamentals (Week 2)

### 2.1 Add Trade-Level Attribution
**Action**: Log entry reason, exit reason, market regime, hypothesis for each trade

### 2.2 Implement Real Slippage Tracking
**Action**: Track fill price vs intended price from Alpaca API

### 2.3 Document Edge Definition
**Action**: Write one-sentence edge definition and validate against baselines

### 2.4 Add Benchmark Comparison
**Action**: Compare vs buy-and-hold SPY and 60/40 portfolio

---

## Phase 3: Risk & Observability (Week 3)

### 3.1 Drawdown Recovery Protocol
**Action**: Document and implement recovery procedures

### 3.2 Signal Decay Monitoring
**Action**: Track RL model performance vs baseline over time

### 3.3 Market Regime Adaptation
**Action**: Implement regime-specific playbooks

---

## Success Metrics

- GitHub Actions: 100% success rate
- Trade Count: 50+ trades
- Win Rate: >40%
- Sharpe Ratio: >0
- Benchmarks: Beat passive strategies
