---
skill_id: anomaly_detector
name: Anomaly Detector
version: 1.0.0
description: Detects execution issues, slippage, and market anomalies in real-time for quality monitoring
author: Trading System CTO
tags: [execution-quality, anomaly-detection, slippage, market-microstructure, monitoring]
tools:
  - detect_execution_anomalies
  - detect_price_gaps
  - monitor_spread_conditions
  - detect_volume_anomalies
  - assess_market_manipulation_risk
dependencies:
  - alpaca-py
  - pandas
  - numpy
integrations:
  - src/core/alpaca_trader.py
---

# Anomaly Detector Skill

Real-time anomaly detection for execution quality, slippage, and market manipulation.

## Overview

This skill provides:
- Execution slippage monitoring
- Price gap detection
- Volume anomalies identification
- Spread widening alerts
- Order fill quality assessment
- Market manipulation detection

## Anomaly Detection Algorithms

### 1. Statistical Methods
- **Z-Score Analysis**: Identify outliers beyond N standard deviations
- **Moving Average Deviation**: Compare to MA with dynamic bands
- **Quantile-based Detection**: Flag values in extreme percentiles

### 2. Machine Learning Models
- **Isolation Forest**: Unsupervised anomaly detection
- **LSTM Autoencoders**: Sequential pattern recognition
- **One-Class SVM**: Boundary detection for normal behavior

### 3. Rule-Based Systems
- **Threshold Rules**: Hard limits on key metrics
- **Pattern Matching**: Known manipulation patterns
- **Time-Series Rules**: Temporal consistency checks

## Tools

### 1. detect_execution_anomalies

Analyzes execution quality and detects slippage issues.

**Parameters:**
- `order_id` (required): Order identifier
- `expected_price` (required): Expected execution price
- `actual_fill_price` (required): Actual fill price
- `quantity` (required): Shares traded
- `order_type` (required): "market" or "limit"
- `timestamp` (required): Execution timestamp (ISO format)

**Returns:**
```json
{
  "success": true,
  "analysis": {
    "order_id": "abc123",
    "slippage": {
      "amount": 0.15,
      "percentage": 0.097,
      "severity": "normal",
      "threshold_exceeded": false
    },
    "execution_quality": {
      "score": 92,
      "grade": "A",
      "comparison_to_vwap": -0.02,
      "comparison_to_midpoint": 0.01
    },
    "cost_analysis": {
      "expected_cost": 5000.00,
      "actual_cost": 5007.50,
      "slippage_cost": 7.50,
      "commission": 0.00,
      "total_cost": 5007.50
    },
    "anomalies_detected": false,
    "warnings": []
  },
  "benchmarks": {
    "typical_slippage_range": [0.05, 0.10],
    "market_conditions": "normal",
    "liquidity_level": "high"
  }
}
```

**Usage:**
```bash
python scripts/anomaly_detector.py detect_execution_anomalies \
    --order-id abc123 \
    --expected-price 155.00 \
    --actual-fill-price 155.15 \
    --quantity 100 \
    --order-type market
```

### 2. detect_price_gaps

Identifies significant price gaps and discontinuities.

**Parameters:**
- `symbol` (required): Trading symbol
- `lookback_periods` (optional): Periods to analyze (default: 100)
- `gap_threshold_pct` (optional): Gap significance threshold (default: 1.0)

**Returns:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "gaps_detected": [
    {
      "timestamp": "2025-11-25T09:30:00Z",
      "type": "gap_up",
      "gap_size_pct": 2.35,
      "prev_close": 150.00,
      "open": 153.53,
      "gap_size_dollars": 3.53,
      "filled": false,
      "volume_ratio": 2.8,
      "catalyst": "Earnings beat expectations",
      "significance": "high",
      "trading_implications": "Strong momentum, expect continuation"
    }
  ],
  "gap_statistics": {
    "total_gaps_30d": 5,
    "gap_fill_rate": 0.60,
    "avg_gap_size": 1.25,
    "largest_unfilled_gap": 2.35
  }
}
```

### 3. monitor_spread_conditions

Monitors bid-ask spreads for liquidity issues.

**Parameters:**
- `symbols` (required): Array of symbols to monitor
- `alert_threshold_pct` (optional): Spread % threshold for alerts (default: 0.5)

**Returns:**
```json
{
  "success": true,
  "spread_analysis": {
    "AAPL": {
      "bid": 154.98,
      "ask": 155.02,
      "spread": 0.04,
      "spread_pct": 0.026,
      "spread_bps": 2.6,
      "status": "normal",
      "liquidity_score": 98,
      "anomalies": []
    }
  },
  "alerts": [],
  "market_conditions": {
    "overall_liquidity": "high",
    "volatility_regime": "low",
    "risk_level": "low"
  }
}
```

### 4. detect_volume_anomalies

Identifies unusual volume patterns.

**Parameters:**
- `symbol` (required): Trading symbol
- `current_volume` (required): Current period volume
- `lookback_periods` (optional): Historical comparison (default: 20)
- `std_dev_threshold` (optional): Standard deviations for anomaly (default: 2.5)

**Returns:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "volume_analysis": {
    "current_volume": 5500000,
    "avg_volume": 3200000,
    "volume_ratio": 1.72,
    "std_deviations": 3.2,
    "anomaly_detected": true,
    "anomaly_type": "high_volume",
    "significance": "high"
  },
  "context": {
    "time_of_day": "09:45",
    "typical_volume_pattern": "Elevated volume common at market open",
    "potential_catalysts": [
      "Earnings announcement",
      "Market-wide surge"
    ]
  },
  "trading_implications": {
    "liquidity": "Excellent",
    "execution_quality": "Expected to be good",
    "caution_level": "Monitor for news"
  }
}
```

### 5. assess_market_manipulation_risk

Screens for potential manipulation patterns.

**Parameters:**
- `symbol` (required): Trading symbol
- `price_data` (required): Array of recent price/volume data
- `sensitivity` (optional): "low", "medium", "high" (default: "medium")

**Returns:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "risk_assessment": {
    "overall_risk": "low",
    "confidence": 0.85,
    "patterns_detected": []
  },
  "screening_results": {
    "spoofing": {
      "detected": false,
      "score": 0.15
    },
    "layering": {
      "detected": false,
      "score": 0.10
    },
    "wash_trading": {
      "detected": false,
      "score": 0.05
    },
    "pump_and_dump": {
      "detected": false,
      "score": 0.08
    }
  },
  "recommendation": "Safe to trade"
}
```

## Slippage Benchmarks

### Expected Slippage by Market Cap
- **Large Cap (>$10B)**: 0.05% - 0.10%
- **Mid Cap ($2B-$10B)**: 0.10% - 0.25%
- **Small Cap (<$2B)**: 0.25% - 0.50%

### Market Condition Adjustments
- **High Volatility**: 2x normal slippage
- **Low Liquidity**: 3x normal slippage
- **Market Open/Close**: 1.5x normal slippage

## Alert Thresholds

### Severity Levels
- **INFO**: Within expected range
- **WARNING**: Exceeds typical by 1.5-2x
- **CRITICAL**: Exceeds typical by >2x or signs of manipulation

### Auto-Actions
- **WARNING**: Log and notify
- **CRITICAL**: Halt trading, notify immediately, save evidence

## Integration Example

```python
from claude_skills import load_skill

anomaly_skill = load_skill("anomaly_detector")

# Monitor execution quality post-trade
execution_analysis = anomaly_skill.detect_execution_anomalies(
    order_id="abc123",
    expected_price=155.00,
    actual_fill_price=155.15,
    quantity=100,
    order_type="market",
    timestamp="2025-11-25T10:15:00Z"
)

if execution_analysis["analysis"]["slippage"]["severity"] == "high":
    alert_team("High slippage detected", execution_analysis)

# Pre-trade checks
spread_check = anomaly_skill.monitor_spread_conditions(
    symbols=["AAPL"],
    alert_threshold_pct=0.3
)

if spread_check["alerts"]:
    delay_trade("Wait for spread normalization")
```

## CLI Usage

```bash
# Detect execution anomalies
python scripts/anomaly_detector.py detect_execution_anomalies \
    --order-id abc123 --expected-price 155.00 --actual-fill-price 155.15

# Detect price gaps
python scripts/anomaly_detector.py detect_price_gaps --symbol AAPL

# Monitor spreads
python scripts/anomaly_detector.py monitor_spread_conditions --symbols AAPL MSFT

# Detect volume anomalies
python scripts/anomaly_detector.py detect_volume_anomalies \
    --symbol AAPL --current-volume 5500000
```

