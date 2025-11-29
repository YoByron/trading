---
skill_id: performance_monitor
name: Performance Monitor
version: 1.0.0
description: Tracks trading performance with comprehensive metrics and analytics including Sharpe ratio, drawdown, and win rate
author: Trading System CTO
tags: [performance, analytics, sharpe-ratio, drawdown, metrics, trading-analytics]
tools:
  - calculate_performance_metrics
  - get_sharpe_ratio
  - calculate_drawdown_analysis
  - get_win_rate_analysis
  - compare_to_benchmark
  - generate_trade_report
dependencies:
  - pandas
  - numpy
  - alpaca-py
integrations:
  - src/core/risk_manager.py::RiskMetrics
---

# Performance Monitor Skill

Comprehensive performance tracking and analytics for trading operations.

## Overview

This skill provides:
- Real-time P&L tracking
- Risk-adjusted return metrics (Sharpe, Sortino, Calmar)
- Drawdown analysis and recovery tracking
- Win rate and trade statistics
- Strategy comparison
- Benchmark comparison (vs SPY, QQQ, etc.)

## Key Performance Metrics

### Return Metrics
- **Total Return**: Overall % gain/loss
- **Annualized Return**: Extrapolated annual return
- **CAGR**: Compound Annual Growth Rate
- **Alpha**: Excess return vs benchmark
- **Beta**: Correlation to market

### Risk Metrics
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
  - < 1.0: Poor
  - 1.0-2.0: Good
  - > 2.0: Excellent
- **Sortino Ratio**: Downside risk-adjusted return
- **Calmar Ratio**: Return / Max Drawdown
- **Max Drawdown**: Largest peak-to-trough decline

### Trade Metrics
- **Win Rate**: % of profitable trades
- **Profit Factor**: Gross Profit / Gross Loss
- **Expectancy**: Average $ per trade
- **Avg Win/Loss Ratio**: Size of wins vs losses

## Tools

### 1. calculate_performance_metrics

Calculates comprehensive performance statistics.

**Parameters:**
- `start_date` (optional): Analysis start date (ISO format YYYY-MM-DD)
- `end_date` (optional): Analysis end date (ISO format YYYY-MM-DD)
- `benchmark_symbol` (optional): Benchmark for comparison (default: "SPY")
- `include_closed_positions` (optional): Include realized P&L only (default: false)

**Returns:**
```json
{
  "success": true,
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-11-25",
    "trading_days": 210
  },
  "returns": {
    "total_return": 0.125,
    "total_return_pct": 12.5,
    "annualized_return": 0.142,
    "cumulative_return": 0.125,
    "benchmark_return": 0.085,
    "alpha": 0.040,
    "beta": 1.15
  },
  "risk_metrics": {
    "sharpe_ratio": 1.85,
    "sortino_ratio": 2.45,
    "calmar_ratio": 3.12,
    "max_drawdown": 0.042,
    "max_drawdown_duration_days": 18,
    "volatility_annualized": 0.165,
    "downside_deviation": 0.092
  },
  "trade_statistics": {
    "total_trades": 156,
    "winning_trades": 94,
    "losing_trades": 62,
    "win_rate": 0.603,
    "avg_win": 125.50,
    "avg_loss": -72.30,
    "largest_win": 850.00,
    "largest_loss": -420.00,
    "avg_win_loss_ratio": 1.74,
    "profit_factor": 2.05,
    "expectancy": 52.80
  },
  "position_analysis": {
    "avg_hold_time_hours": 36.5,
    "longest_winning_streak": 8,
    "longest_losing_streak": 4,
    "current_streak": {
      "type": "winning",
      "length": 3
    }
  },
  "equity_curve": {
    "starting_equity": 100000,
    "current_equity": 112500,
    "peak_equity": 115200,
    "trough_equity": 98200
  }
}
```

**Usage:**
```bash
python scripts/performance_monitor.py calculate_performance_metrics \
    --start-date 2025-01-01 \
    --end-date 2025-11-25 \
    --benchmark-symbol SPY
```

### 2. get_sharpe_ratio

Calculates Sharpe ratio for risk-adjusted returns.

**Parameters:**
- `returns` (required): Array of period returns
- `risk_free_rate` (optional): Annual risk-free rate (default: 0.045)
- `periods_per_year` (optional): Trading periods per year (default: 252)

**Returns:**
```json
{
  "success": true,
  "sharpe_ratio": 1.85,
  "calculation": {
    "mean_return": 0.00089,
    "std_dev": 0.0105,
    "risk_free_rate_daily": 0.000178,
    "excess_return": 0.000712,
    "annualized_sharpe": 1.85
  },
  "interpretation": {
    "rating": "good",
    "description": "Above 1.5 indicates strong risk-adjusted returns"
  }
}
```

### 3. calculate_drawdown_analysis

Analyzes drawdown patterns and recovery times.

**Parameters:**
- `equity_curve` (required): Array of equity values over time
- `rolling_window_days` (optional): Rolling max window (default: 252)

**Returns:**
```json
{
  "success": true,
  "drawdown_analysis": {
    "max_drawdown": {
      "amount": 4200.00,
      "percentage": 4.2,
      "peak_value": 115200,
      "trough_value": 111000,
      "peak_date": "2025-08-15",
      "trough_date": "2025-09-02",
      "recovery_date": "2025-09-28",
      "duration_days": 18,
      "recovery_days": 26,
      "total_duration_days": 44
    },
    "current_drawdown": {
      "amount": 2700.00,
      "percentage": 2.34,
      "days_in_drawdown": 8
    },
    "drawdown_distribution": {
      "num_drawdowns": 12,
      "avg_drawdown_pct": 1.8,
      "avg_duration_days": 9.5,
      "avg_recovery_days": 15.2
    },
    "historical_drawdowns": [
      {
        "percentage": 4.2,
        "start_date": "2025-08-15",
        "end_date": "2025-09-28",
        "duration_days": 44
      }
    ]
  },
  "risk_assessment": {
    "drawdown_severity": "moderate",
    "recovery_speed": "fast",
    "overall_risk": "acceptable"
  }
}
```

### 4. get_win_rate_analysis

Analyzes win rate trends and patterns.

**Parameters:**
- `trades` (required): Array of trade history objects
- `grouping` (optional): "daily", "weekly", "monthly", "strategy" (default: "monthly")
- `min_sample_size` (optional): Minimum trades for valid stat (default: 20)

**Returns:**
```json
{
  "success": true,
  "overall": {
    "win_rate": 0.603,
    "total_trades": 156,
    "winning_trades": 94,
    "losing_trades": 62,
    "confidence_interval_95": [0.52, 0.68]
  },
  "by_strategy": {
    "core_strategy": {
      "win_rate": 0.65,
      "trades": 105,
      "wins": 68,
      "losses": 37
    },
    "growth_strategy": {
      "win_rate": 0.52,
      "trades": 51,
      "wins": 26,
      "losses": 25
    }
  },
  "by_time_period": {
    "month_1": {"win_rate": 0.58, "trades": 35},
    "month_2": {"win_rate": 0.62, "trades": 38},
    "month_3": {"win_rate": 0.61, "trades": 40}
  },
  "trends": {
    "direction": "improving",
    "statistical_significance": true,
    "regression_slope": 0.008
  }
}
```

### 5. compare_to_benchmark

Compares strategy performance to market benchmark.

**Parameters:**
- `portfolio_returns` (required): Array of portfolio returns
- `benchmark_symbol` (optional): Benchmark ticker (default: "SPY")
- `start_date` (required): ISO format date
- `end_date` (required): ISO format date

**Returns:**
```json
{
  "success": true,
  "comparison": {
    "portfolio": {
      "total_return": 0.125,
      "annualized_return": 0.142,
      "volatility": 0.165,
      "sharpe_ratio": 1.85,
      "max_drawdown": 0.042
    },
    "benchmark": {
      "symbol": "SPY",
      "total_return": 0.085,
      "annualized_return": 0.095,
      "volatility": 0.145,
      "sharpe_ratio": 1.32,
      "max_drawdown": 0.068
    },
    "relative_performance": {
      "alpha": 0.047,
      "beta": 1.15,
      "tracking_error": 0.042,
      "information_ratio": 1.12,
      "outperformance": 0.040,
      "outperformance_pct": 47.1
    }
  },
  "interpretation": {
    "verdict": "outperforming",
    "confidence": "high",
    "key_insights": [
      "Higher risk-adjusted returns (Sharpe 1.85 vs 1.32)",
      "Lower maximum drawdown (4.2% vs 6.8%)",
      "Positive alpha indicates skill beyond market beta"
    ]
  }
}
```

### 6. generate_trade_report

Generates detailed trade-by-trade performance report.

**Parameters:**
- `start_date` (optional): Report start date
- `end_date` (optional): Report end date
- `filter_strategy` (optional): Filter by specific strategy
- `min_pnl` (optional): Filter by minimum P&L
- `sort_by` (optional): "date", "pnl", "return_pct" (default: "date")

**Returns:**
```json
{
  "success": true,
  "summary": {
    "total_trades": 156,
    "period": "2025-01-01 to 2025-11-25",
    "total_pnl": 12500.00,
    "avg_pnl": 80.13
  },
  "trades": [
    {
      "trade_id": "t001",
      "symbol": "AAPL",
      "strategy": "core_strategy",
      "entry_date": "2025-11-24",
      "exit_date": "2025-11-25",
      "entry_price": 152.50,
      "exit_price": 155.75,
      "quantity": 50,
      "pnl": 162.50,
      "return_pct": 2.13,
      "hold_time_hours": 24.5,
      "execution_quality": "good"
    }
  ],
  "best_trades": [
    {"symbol": "NVDA", "pnl": 850.00, "return_pct": 8.5}
  ],
  "worst_trades": [
    {"symbol": "META", "pnl": -420.00, "return_pct": -4.2}
  ]
}
```

## Benchmarks

### Industry Standards
- **Hedge Fund Average**: Sharpe ~1.0, Return 8-12%
- **Top Quartile**: Sharpe >1.5, Return >15%
- **S&P 500**: Sharpe ~0.8-1.0, Return ~10% annually

### Your Targets
- Sharpe Ratio: >1.5
- Max Drawdown: <10%
- Win Rate: >55%
- Alpha: >3%

## Integration Example

```python
from claude_skills import load_skill

perf_skill = load_skill("performance_monitor")

# Daily performance review
metrics = perf_skill.calculate_performance_metrics(
    start_date="2025-11-01",
    end_date="2025-11-25",
    benchmark_symbol="SPY"
)

print(f"Sharpe Ratio: {metrics['risk_metrics']['sharpe_ratio']}")
print(f"Win Rate: {metrics['trade_statistics']['win_rate']*100}%")

# Check if meeting targets
if metrics["risk_metrics"]["sharpe_ratio"] < 1.5:
    alert("Performance below target Sharpe ratio")

# Detailed drawdown analysis
dd_analysis = perf_skill.calculate_drawdown_analysis(
    equity_curve=get_equity_data()
)
if dd_analysis["current_drawdown"]["percentage"] > 5:
    alert("In significant drawdown - review risk controls")
```

## CLI Usage

```bash
# Calculate performance metrics
python scripts/performance_monitor.py calculate_performance_metrics \
    --start-date 2025-01-01 --end-date 2025-11-25

# Get Sharpe ratio
python scripts/performance_monitor.py get_sharpe_ratio \
    --returns-file returns.json

# Generate trade report
python scripts/performance_monitor.py generate_trade_report \
    --start-date 2025-11-01 --sort-by pnl
```

## Visualization Support

The skill includes data formatted for:
- Equity curve charts
- Drawdown charts
- Monthly return heatmaps
- Strategy comparison charts
- Trade distribution histograms
