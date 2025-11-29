# Drawdown Recovery Protocol

## Purpose

Documented protocol for responding to drawdowns and implementing circuit breakers beyond hard limits.

## Drawdown Levels & Responses

### Level 1: Minor Drawdown (< 2%)
**Status**: Normal market fluctuation
**Action**: Continue trading, monitor closely
**Circuit Breaker**: None

### Level 2: Moderate Drawdown (2-5%)
**Status**: ⚠️ Warning
**Action**:
- Reduce position sizes by 50%
- Increase stop-loss frequency checks
- Review recent trades for patterns
- Consider pausing new entries for 1-2 days

**Circuit Breaker**: None

### Level 3: Significant Drawdown (5-10%)
**Status**: 🚨 Alert
**Action**:
- **IMMEDIATE**: Reduce all position sizes by 75%
- Pause new entries for 3-5 days
- Run post-mortem on all losing trades
- Review strategy edge validity
- Consider switching to defensive mode (bonds/cash)

**Circuit Breaker**: Auto-reduce position sizing

### Level 4: Severe Drawdown (10-20%)
**Status**: 🚨 CRITICAL
**Action**:
- **IMMEDIATE**: Close all positions
- **IMMEDIATE**: Pause all trading for 7-14 days
- Full strategy review
- Validate edge still exists
- Consider strategy pivot

**Circuit Breaker**: Auto-pause trading

### Level 5: Extreme Drawdown (> 20%)
**Status**: 🚨 EMERGENCY
**Action**:
- **IMMEDIATE**: Close all positions
- **IMMEDIATE**: Pause trading indefinitely
- Full system audit
- Strategy redesign required
- May need to restart with new approach

**Circuit Breaker**: Hard stop - manual restart required

## Recovery Process

### Phase 1: Assessment (Days 1-3)
1. Calculate exact drawdown amount
2. Identify contributing factors
3. Review trade log for patterns
4. Check if edge still valid

### Phase 2: Analysis (Days 4-7)
1. Post-mortem on losing trades
2. Compare against benchmarks
3. Validate strategy assumptions
4. Identify root causes

### Phase 3: Recovery (Days 8+)
1. Implement fixes
2. Test with paper trading
3. Gradually resume with reduced sizing
4. Monitor closely

## Circuit Breaker Implementation

### Automatic Triggers
- Drawdown > 5%: Auto-reduce sizing
- Drawdown > 10%: Auto-pause trading
- 3 consecutive losses: Reduce sizing by 25%
- 5 consecutive losses: Pause for 1 day

### Manual Overrides
- CEO/CTO can manually pause/resume
- Emergency stop button in dashboard
- GitHub Actions workflow can be disabled

## Current Status

**Current Drawdown**: 0.06% (Level 1 - Normal)
**Status**: ✅ No action required
**Last Review**: 2025-11-29

## Monitoring

- Daily drawdown calculation
- Alert on Level 2+ drawdowns
- Weekly recovery progress review
- Monthly protocol effectiveness review
