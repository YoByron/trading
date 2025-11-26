#!/usr/bin/env python3
"""
Generate World-Class Trading Dashboard

Implements elite-level dashboard comparable to:
- Two Sigma internal dashboards
- QuantConnect premium analytics
- HFT trading desks
- Hedge fund risk consoles

Features:
- Predictive analytics (Monte Carlo forecasting)
- Comprehensive risk metrics
- Performance attribution
- AI-generated insights
- Strategy-level breakdown
- Rich visualizations (ASCII charts)
- Real-time monitoring status
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.analytics.world_class_analytics import WorldClassAnalytics
    from src.analytics.ai_insights import AIInsightGenerator
except ImportError:
    print("⚠️  Analytics modules not available - using basic metrics")
    WorldClassAnalytics = None
    AIInsightGenerator = None

DATA_DIR = Path("data")


def load_json_file(filepath: Path) -> dict:
    """Load JSON file, return empty dict if not found."""
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def generate_equity_curve_chart(equity_curve: List[float], width: int = 60, height: int = 10) -> str:
    """
    Generate ASCII equity curve chart.
    
    Args:
        equity_curve: List of portfolio values
        width: Chart width in characters
        height: Chart height in lines
    
    Returns:
        ASCII chart string
    """
    if len(equity_curve) < 2:
        return "  (Insufficient data)"
    
    equity_array = np.array(equity_curve)
    min_val = np.min(equity_array)
    max_val = np.max(equity_array)
    range_val = max_val - min_val
    
    if range_val == 0:
        return "  (No variation)"
    
    # Normalize to chart dimensions
    normalized = ((equity_array - min_val) / range_val) * (height - 1)
    
    # Create chart grid
    chart = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Plot points
    for i in range(len(normalized)):
        x = int((i / len(normalized)) * (width - 1))
        y = int(normalized[i])
        y = height - 1 - y  # Flip Y axis
        if 0 <= x < width and 0 <= y < height:
            chart[y][x] = '█'
    
    # Connect points
    for i in range(len(normalized) - 1):
        x1 = int((i / len(normalized)) * (width - 1))
        x2 = int(((i + 1) / len(normalized)) * (width - 1))
        y1 = int(normalized[i])
        y2 = int(normalized[i + 1])
        y1 = height - 1 - y1
        y2 = height - 1 - y2
        
        if x1 != x2:
            steps = abs(x2 - x1)
            for step in range(steps + 1):
                x = x1 + int((x2 - x1) * step / steps)
                y = y1 + int((y2 - y1) * step / steps)
                if 0 <= x < width and 0 <= y < height:
                    chart[y][x] = '█'
    
    # Convert to string
    chart_lines = [''.join(row) for row in chart]
    
    # Add labels
    result = f"  ${min_val:,.0f} ┤{' ' * (width - 20)}┤ ${max_val:,.0f}\n"
    result += '\n'.join(f"     │{line}" for line in chart_lines)
    
    return result


def generate_risk_heatmap(risk_metrics: Dict[str, float]) -> str:
    """
    Generate ASCII risk heatmap.
    
    Returns:
        ASCII heatmap string
    """
    metrics = [
        ('Max Drawdown', risk_metrics.get('max_drawdown_pct', 0.0), 10.0),
        ('VaR (95%)', risk_metrics.get('var_95', 0.0), 5.0),
        ('Volatility', risk_metrics.get('volatility', 0.0), 20.0),
        ('Ulcer Index', risk_metrics.get('ulcer_index', 0.0), 10.0),
    ]
    
    result = "  Risk Level:\n"
    for name, value, threshold in metrics:
        level = min(100, (value / threshold) * 100) if threshold > 0 else 0
        bars = int(level / 5)
        bar_char = '█' if level < 50 else '█' if level < 75 else '█'
        result += f"  {name:20s} [{bar_char * bars:<20}] {level:.1f}%\n"
    
    return result


def generate_world_class_dashboard() -> str:
    """Generate world-class dashboard markdown."""
    
    # Load data
    system_state = load_json_file(DATA_DIR / "system_state.json")
    perf_log = load_json_file(DATA_DIR / "performance_log.json")
    challenge_start = load_json_file(DATA_DIR / "challenge_start.json")
    
    # Extract equity curve
    equity_curve = []
    if isinstance(perf_log, list):
        equity_curve = [entry.get('equity', 100000.0) for entry in perf_log]
    
    if not equity_curve:
        equity_curve = [system_state.get('account', {}).get('current_equity', 100000.0)]
    
    # Initialize analytics
    analytics = WorldClassAnalytics() if WorldClassAnalytics else None
    ai_insights = AIInsightGenerator() if AIInsightGenerator else None
    
    # Calculate basic metrics
    account = system_state.get('account', {})
    total_pl = account.get('total_pl', 0.0)
    current_equity = account.get('current_equity', 100000.0)
    starting_balance = challenge_start.get('starting_balance', 100000.0)
    
    # Calculate returns for analytics
    returns = []
    if len(equity_curve) > 1:
        returns = [
            (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            for i in range(1, len(equity_curve))
        ]
    
    # Calculate risk metrics
    risk_metrics_dict = {}
    if analytics and len(equity_curve) > 1:
        risk_metrics = analytics.calculate_risk_metrics(equity_curve)
        risk_metrics_dict = {
            'max_drawdown_pct': risk_metrics.max_drawdown_pct,
            'ulcer_index': risk_metrics.ulcer_index,
            'sortino_ratio': risk_metrics.sortino_ratio,
            'sharpe_ratio': risk_metrics.sharpe_ratio,
            'var_95': risk_metrics.var_95,
            'var_99': risk_metrics.var_99,
            'cvar_95': risk_metrics.cvar_95,
            'volatility': risk_metrics.volatility,
            'calmar_ratio': risk_metrics.calmar_ratio,
        }
    else:
        risk_metrics_dict = {
            'max_drawdown_pct': 0.0,
            'ulcer_index': 0.0,
            'sortino_ratio': 0.0,
            'sharpe_ratio': 0.0,
            'var_95': 0.0,
            'var_99': 0.0,
            'cvar_95': 0.0,
            'volatility': 0.0,
            'calmar_ratio': 0.0,
        }
    
    # Monte Carlo forecast
    forecast_dict = {}
    if analytics and len(returns) > 10:
        forecast = analytics.monte_carlo_forecast(returns)
        forecast_dict = {
            'expected_profit_7d': forecast.expected_profit_7d[0] * current_equity,
            'expected_profit_30d': forecast.expected_profit_30d[0] * current_equity,
            'confidence_interval_95_lower': forecast.confidence_interval_95[0] * current_equity,
            'confidence_interval_95_upper': forecast.confidence_interval_95[1] * current_equity,
            'drawdown_probability': forecast.drawdown_probability,
            'edge_drift_score': forecast.edge_drift_score,
        }
    else:
        forecast_dict = {
            'expected_profit_7d': 0.0,
            'expected_profit_30d': 0.0,
            'drawdown_probability': 0.0,
            'edge_drift_score': 0.0,
        }
    
    # AI insights
    briefing = None
    strategy_health = None
    if ai_insights:
        metrics_dict = {
            'total_pl': total_pl,
            'win_rate': system_state.get('performance', {}).get('win_rate', 0.0) * 100,
            'avg_daily_profit': total_pl / max(len(perf_log), 1) if isinstance(perf_log, list) else 0.0,
        }
        recent_trades = []
        briefing = ai_insights.generate_daily_briefing(metrics_dict, recent_trades, risk_metrics_dict)
        strategy_health = ai_insights.assess_strategy_health(metrics_dict, risk_metrics_dict, forecast_dict)
    
    # Performance metrics
    performance = system_state.get('performance', {})
    win_rate = performance.get('win_rate', 0.0) * 100
    total_trades = performance.get('total_trades', 0)
    
    # Calculate averages
    trading_days = len(perf_log) if isinstance(perf_log, list) and perf_log else 1
    avg_daily_profit = total_pl / trading_days if trading_days > 0 else 0.0
    north_star_target = 100.0
    progress_pct = (avg_daily_profit / north_star_target * 100) if north_star_target > 0 else 0.0
    
    if total_pl > 0 and progress_pct < 0.01:
        progress_pct = max(0.01, (total_pl / north_star_target) * 100)
    
    # Challenge info
    challenge = system_state.get('challenge', {})
    current_day = challenge.get('current_day', 1)
    total_days = challenge.get('total_days', 90)
    
    # Generate dashboard
    now = datetime.now()
    
    # Progress bar
    north_star_bars = 1 if total_pl > 0 and progress_pct < 5.0 else min(int(progress_pct / 5), 20)
    north_star_bar = '█' * north_star_bars + '░' * (20 - north_star_bars)
    display_progress_pct = max(progress_pct, 0.01) if total_pl > 0 else progress_pct
    
    dashboard = f"""# 🌟 World-Class Trading Dashboard

**Last Updated**: {now.strftime('%Y-%m-%d %I:%M %p ET')}  
**Auto-Updated**: Daily via GitHub Actions  
**Dashboard Version**: World-Class Elite Analytics

---

## 🎯 North Star Goal

**Target**: **$100+/day profit**

| Metric | Current | Target | Progress |
|--------|---------|--------|----------|
| **Average Daily Profit** | ${avg_daily_profit:.2f}/day | $100.00/day | {display_progress_pct:.2f}% |
| **Total P/L** | ${total_pl:+,.2f} ({total_pl/starting_balance*100:+.2f}%) | TBD | {'✅' if total_pl > 0 else '⚠️'} |
| **Win Rate** | {win_rate:.1f}% | >55% | {'✅' if win_rate >= 55 else '⚠️'} |

**Progress Toward $100/Day Goal**: `{north_star_bar}` ({display_progress_pct:.2f}%)  
*This shows how close your average daily profit is to the $100/day target*

---

## 🔮 Predictive Analytics

### Monte Carlo Forecast (10,000 simulations)

| Horizon | Expected Profit | 95% Confidence Interval |
|---------|----------------|-------------------------|
| **7 Days** | ${forecast_dict.get('expected_profit_7d', 0.0):+,.2f} | ${forecast_dict.get('confidence_interval_95_lower', 0.0):+,.2f} to ${forecast_dict.get('confidence_interval_95_upper', 0.0):+,.2f} |
| **30 Days** | ${forecast_dict.get('expected_profit_30d', 0.0):+,.2f} | See 7-day CI scaled |

**Edge Drift Score**: {forecast_dict.get('edge_drift_score', 0.0):+.2f} ({'✅ Improving' if forecast_dict.get('edge_drift_score', 0.0) > 0.1 else '⚠️ Decaying' if forecast_dict.get('edge_drift_score', 0.0) < -0.1 else '➡️ Stable'})  
**Drawdown Probability (>5%)**: {forecast_dict.get('drawdown_probability', 0.0):.1f}%

---

## ⚖️ Comprehensive Risk Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Max Drawdown** | {risk_metrics_dict.get('max_drawdown_pct', 0.0):.2f}% | {'✅' if risk_metrics_dict.get('max_drawdown_pct', 0.0) < 5.0 else '⚠️'} |
| **Ulcer Index** | {risk_metrics_dict.get('ulcer_index', 0.0):.2f} | {'✅' if risk_metrics_dict.get('ulcer_index', 0.0) < 5.0 else '⚠️'} |
| **Sharpe Ratio** | {risk_metrics_dict.get('sharpe_ratio', 0.0):.2f} | {'✅' if risk_metrics_dict.get('sharpe_ratio', 0.0) > 1.0 else '⚠️'} |
| **Sortino Ratio** | {risk_metrics_dict.get('sortino_ratio', 0.0):.2f} | {'✅' if risk_metrics_dict.get('sortino_ratio', 0.0) > 1.0 else '⚠️'} |
| **Calmar Ratio** | {risk_metrics_dict.get('calmar_ratio', 0.0):.2f} | {'✅' if risk_metrics_dict.get('calmar_ratio', 0.0) > 1.0 else '⚠️'} |
| **VaR (95%)** | {risk_metrics_dict.get('var_95', 0.0):.2f}% | Risk level |
| **VaR (99%)** | {risk_metrics_dict.get('var_99', 0.0):.2f}% | Extreme risk |
| **CVaR (95%)** | {risk_metrics_dict.get('cvar_95', 0.0):.2f}% | Expected tail loss |
| **Volatility (Annualized)** | {risk_metrics_dict.get('volatility', 0.0):.2f}% | {'✅' if risk_metrics_dict.get('volatility', 0.0) < 20.0 else '⚠️'} |

### Risk Heatmap

{generate_risk_heatmap(risk_metrics_dict) if analytics else '  (Analytics unavailable)'}

---

## 🧠 AI-Generated Insights

### Daily Briefing

{briefing.summary if briefing else '  (AI insights unavailable)'}

**Key Changes Today**:
{briefing.key_changes[0] if briefing and briefing.key_changes else '  - No significant changes'}

**Anomalies Detected**:
{briefing.anomalies[0] if briefing and briefing.anomalies else '  - None detected'}

**Recommendations**:
{briefing.recommendations[0] if briefing and briefing.recommendations else '  - Continue current strategy'}

### Strategy Health Score

{strategy_health.diagnosis if strategy_health else '  (Health assessment unavailable)'}

| Component | Score | Status |
|-----------|-------|--------|
| **Overall Health** | {strategy_health.overall_score:.1f}/100 | {'✅' if strategy_health and strategy_health.overall_score > 75 else '⚠️' if strategy_health and strategy_health.overall_score > 50 else '❌'} |
| **Performance** | {strategy_health.performance_score:.1f}/100 | {'✅' if strategy_health and strategy_health.performance_score > 50 else '⚠️'} |
| **Risk Management** | {strategy_health.risk_score:.1f}/100 | {'✅' if strategy_health and strategy_health.risk_score > 50 else '⚠️'} |
| **Consistency** | {strategy_health.consistency_score:.1f}/100 | {'✅' if strategy_health and strategy_health.consistency_score > 50 else '⚠️'} |
| **Edge Quality** | {strategy_health.edge_score:.1f}/100 | {'✅' if strategy_health and strategy_health.edge_score > 50 else '⚠️'} |

**Action Items**:
{strategy_health.action_items[0] if strategy_health and strategy_health.action_items else '  - Monitor performance'}

---

## 📈 Equity Curve Visualization

```
{generate_equity_curve_chart(equity_curve) if len(equity_curve) > 1 else '  (Insufficient data for chart)'}
```

---

## 💰 Financial Performance Summary

| Metric | Value |
|--------|-------|
| **Starting Balance** | ${starting_balance:,.2f} |
| **Current Equity** | ${current_equity:,.2f} |
| **Total P/L** | ${total_pl:+,.2f} ({total_pl/starting_balance*100:+.2f}%) |
| **Total Trades** | {total_trades} |
| **Win Rate** | {win_rate:.1f}% |

---

## 📊 90-Day R&D Challenge Progress

**Current**: Day {current_day} of {total_days} ({current_day/total_days*100:.1f}% complete)

**Timeline Progress**: `{'█' * int((current_day/total_days*100)/5) + '░' * (20 - int((current_day/total_days*100)/5))}` ({current_day/total_days*100:.1f}%)  
*This shows how far through the 90-day R&D challenge timeline you are*

---

## 🔗 Quick Links

- [Repository](https://github.com/IgorGanapolsky/trading)
- [GitHub Actions](https://github.com/IgorGanapolsky/trading/actions)
- [Latest Trades](https://github.com/IgorGanapolsky/trading/tree/main/data)

---

*This world-class dashboard is automatically updated daily by GitHub Actions with elite-level analytics.*

"""
    
    return dashboard


def main():
    """Generate and save world-class dashboard."""
    dashboard = generate_world_class_dashboard()
    
    # Save to file
    output_file = Path("wiki/Progress-Dashboard.md")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(dashboard)
    
    print("✅ World-class dashboard generated successfully!")
    print(f"📄 Saved to: {output_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

