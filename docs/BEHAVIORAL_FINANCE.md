# Behavioral Finance Integration - Jason Zweig Principles

**Based on**: "Your Money and Your Brain" by Jason Zweig  
**Implementation Date**: November 24, 2025  
**Purpose**: Prevent psychological biases from affecting trading decisions

---

## Overview

This system implements key principles from behavioral finance to prevent common psychological biases that lead to poor investment decisions. The behavioral finance module tracks emotions, expectations, patterns, and decision-making history to ensure rational, systematic trading.

---

## Key Principles Implemented

### 1. **Emotional Control** ✅

**Principle**: Our brains process financial risks similarly to life-threatening situations, causing emotions like fear and greed to override rational thinking.

**Implementation**:
- **Emotional Registry**: Tracks emotional responses to trading events
- **Emotional State Monitoring**: Checks current emotional state before trades
- **Circuit Breakers**: Pauses trading when fear/panic intensity > 0.7 or euphoria > 0.8
- **Automated Decision Making**: Reduces emotional interference through systematic processes

**Usage**:
```python
from src.core.behavioral_finance import BehavioralFinanceManager

bf_manager = BehavioralFinanceManager()
emotion, intensity = bf_manager.check_emotional_state()

if emotion == EmotionalState.PANIC and intensity > 0.7:
    # Pause trading
    pass
```

---

### 2. **Anticipation vs. Reality** ✅

**Principle**: The anticipation of financial rewards often triggers euphoria, but actual rewards may not provide the same satisfaction. This can lead to impulsive decisions.

**Implementation**:
- **Trade Expectation Tracking**: Records expected returns and confidence before trades
- **Outcome Comparison**: Compares expected vs actual returns
- **Expectation Gap Analysis**: Calculates gaps to identify overconfidence
- **Emotional Response Recording**: Records emotional responses based on expectation gaps

**Usage**:
```python
# Before trade
expectation = bf_manager.record_trade_expectation(
    symbol="SPY",
    expected_return_pct=5.0,
    expected_confidence=0.75,
    entry_price=450.0,
)

# After trade
bf_manager.update_trade_outcome(
    expectation=expectation,
    exit_price=455.0,
    actual_return_pct=1.11,  # Actual return
)
# System automatically calculates expectation gap and records emotions
```

---

### 3. **Pattern Recognition Bias** ✅

**Principle**: Humans are wired to detect patterns, sometimes perceiving trends where none exist. This can result in overconfidence and misguided investment choices.

**Implementation**:
- **Pattern Validation**: Requires minimum sample size (20) before accepting high-confidence patterns
- **Historical Success Rate Tracking**: Tracks success rates of different pattern types
- **Confidence Adjustment**: Reduces confidence if historical success rate is low
- **Pattern History**: Maintains database of pattern checks and outcomes

**Usage**:
```python
# Check pattern before using it
is_valid, reason = bf_manager.check_pattern_recognition_bias(
    pattern_type="momentum",
    detected_pattern="SPY showing strong momentum",
    confidence=0.85,
)

if not is_valid:
    # Pattern rejected - adjust strategy
    pass

# After trade outcome is known
bf_manager.update_pattern_outcome(
    pattern_type="momentum",
    was_successful=True,
)
```

---

### 4. **Loss Aversion** ✅

**Principle**: People feel the pain of losses more intensely than the pleasure of equivalent gains, leading to overly conservative behaviors.

**Implementation**:
- **Loss Threshold Detection**: Monitors when losses exceed threshold (-2%)
- **Fear Response Tracking**: Counts fear responses in recent decisions
- **Overconservatism Warning**: Alerts when becoming too conservative after losses
- **Balanced Approach**: Prevents overreaction to losses while maintaining risk controls

**Usage**:
```python
should_trade, reason = bf_manager.check_loss_aversion(
    recent_losses=[-0.02, -0.015, -0.01],  # Recent loss percentages
    account_value=10000.0,
    daily_pl=-50.0,
)

if "overconservatism" in reason:
    # Warning: Don't become too conservative
    pass
```

---

### 5. **Automation** ✅

**Principle**: Implement automated systems to reduce emotional interference in decision-making.

**Implementation**:
- **Integrated with Risk Manager**: Behavioral checks automatically run during trade validation
- **Systematic Processes**: All checks are automated and systematic
- **No Manual Override**: Prevents emotional overrides of rational decisions

**Integration**:
```python
from src.core.risk_manager import RiskManager

risk_manager = RiskManager(
    use_behavioral_finance=True,  # Enable behavioral finance
    data_dir="data",
)

# Behavioral checks automatically run in validate_trade()
validation = risk_manager.validate_trade(
    symbol="SPY",
    amount=100.0,
    sentiment_score=0.7,
    account_value=10000.0,
    expected_return_pct=5.0,
    confidence=0.75,
    pattern_type="momentum",
)
```

---

### 6. **Diversification** ✅

**Principle**: Diversification helps mitigate risks and prevents overexposure to any single asset.

**Implementation**:
- **Position Size Limits**: Already implemented in RiskManager (max 10% per position)
- **Concentration Monitoring**: Tracks portfolio concentration
- **Automatic Rebalancing**: Monthly rebalancing checks

---

### 7. **Realistic Goals** ✅

**Principle**: Establish achievable objectives and maintain realistic expectations.

**Implementation**:
- **Expectation Tracking**: Records expected returns for comparison
- **Gap Analysis**: Identifies when expectations are unrealistic
- **Goal Validation**: Ensures goals are achievable based on historical performance

---

### 8. **Emotional Registry** ✅

**Principle**: Keep a record of emotional responses to various financial decisions to identify patterns and improve future decision-making.

**Implementation**:
- **Comprehensive Logging**: Records all emotional responses with timestamps
- **Pattern Analysis**: Identifies emotional patterns over time
- **Decision Correlation**: Links emotions to decision outcomes
- **Persistent Storage**: Saves emotional registry to disk for analysis

**Data Structure**:
```python
{
    "timestamp": "2025-11-24T10:30:00",
    "event_type": "trade_execution",
    "symbol": "SPY",
    "emotional_state": "fear",
    "intensity": 0.65,
    "decision_made": "Executed buy order",
    "outcome": "pending",
    "notes": "High volatility day"
}
```

---

## Integration Points

### Risk Manager Integration

The behavioral finance module is integrated into the `RiskManager` class:

```python
risk_manager = RiskManager(
    use_behavioral_finance=True,  # Enable behavioral finance
    data_dir="data",
)

# Behavioral checks run automatically in validate_trade()
validation = risk_manager.validate_trade(
    symbol="SPY",
    amount=100.0,
    sentiment_score=0.7,
    account_value=10000.0,
    expected_return_pct=5.0,      # For expectation tracking
    confidence=0.75,               # For pattern bias checks
    pattern_type="momentum",       # For pattern validation
)
```

### Strategy Integration

Strategies can record expectations before trades:

```python
# In strategy execution
expectation = risk_manager.record_trade_expectation(
    symbol=selected_symbol,
    expected_return_pct=expected_return,
    expected_confidence=confidence,
    entry_price=entry_price,
)

# Execute trade...

# After trade closes
risk_manager.update_trade_outcome(
    expectation=expectation,
    exit_price=exit_price,
    actual_return_pct=actual_return,
)
```

---

## Behavioral Finance Summary

Get a summary of behavioral finance metrics:

```python
summary = risk_manager.get_behavioral_summary()

# Returns:
{
    "dominant_emotion": "neutral",
    "emotion_intensity": 0.25,
    "total_expectations": 50,
    "completed_expectations": 45,
    "avg_expectation_gap": -0.5,  # Actual was 0.5% worse than expected
    "pattern_success_rates": {
        "momentum": 0.65,
        "reversal": 0.45,
    },
    "total_emotional_records": 120,
    "recent_emotions": [...]
}
```

---

## Data Storage

Behavioral finance data is stored in JSON files in the `data/` directory:

- `data/behavioral_expectations.json` - Trade expectations and outcomes
- `data/behavioral_emotions.json` - Emotional registry
- `data/behavioral_patterns.json` - Pattern validation history

All data persists across sessions and is automatically loaded on initialization.

---

## Configuration

Behavioral finance can be configured when initializing the RiskManager:

```python
risk_manager = RiskManager(
    max_daily_loss_pct=2.0,
    max_position_size_pct=10.0,
    max_drawdown_pct=10.0,
    max_consecutive_losses=3,
    use_behavioral_finance=True,      # Enable/disable
    data_dir="data",                  # Data storage directory
)

# Or configure BehavioralFinanceManager directly:
from src.core.behavioral_finance import BehavioralFinanceManager

bf_manager = BehavioralFinanceManager(
    data_dir="data",
    max_pattern_confidence=0.7,        # Max confidence without validation
    min_pattern_sample_size=20,        # Min samples for pattern validation
    loss_aversion_threshold=-0.02,     # Loss % that triggers checks
)
```

---

## Benefits

1. **Prevents Emotional Decisions**: Automatically pauses trading when emotions are too high
2. **Tracks Expectations**: Identifies when expectations are unrealistic
3. **Validates Patterns**: Prevents overconfidence in perceived patterns
4. **Manages Loss Aversion**: Prevents becoming overly conservative after losses
5. **Improves Decision Making**: Learns from past decisions and outcomes
6. **Systematic Approach**: Ensures consistent, rational decision-making

---

## Future Enhancements

- Machine learning models to predict emotional states
- Advanced pattern recognition with statistical validation
- Integration with reinforcement learning agents
- Real-time emotional state dashboard
- Automated goal adjustment based on performance

---

## References

- Zweig, Jason. "Your Money and Your Brain: How the New Science of Neuroeconomics Can Help Make You Rich." Simon & Schuster, 2007.
- Behavioral Finance Research Papers
- Neuroeconomics Studies

---

**Last Updated**: November 24, 2025

