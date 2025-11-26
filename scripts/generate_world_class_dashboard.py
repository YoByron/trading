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
- Performance attribution by strategy/asset
- AI-generated insights with trade analysis
- Strategy-level breakdown
- Rich visualizations (ASCII charts)
- Real-time monitoring status
- Actionable risk alerts
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

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


def load_trade_data() -> List[Dict[str, Any]]:
    """Load all trade data from trade log files."""
    trades = []
    
    # Load from daily trade files
    trade_files = sorted(DATA_DIR.glob("trades_*.json"))
    for trade_file in trade_files:
        try:
            with open(trade_file, 'r') as f:
                daily_trades = json.load(f)
                if isinstance(daily_trades, list):
                    trades.extend(daily_trades)
                elif isinstance(daily_trades, dict):
                    trades.append(daily_trades)
        except Exception:
            continue
    
    return trades


def calculate_win_rate_from_trades(trades: List[Dict[str, Any]]) -> Tuple[float, int, int]:
    """
    Calculate win rate from actual trade data.
    
    Returns:
        (win_rate_pct, winning_trades, total_closed_trades)
    """
    closed_trades = [t for t in trades if t.get('status') == 'filled' and t.get('pl') is not None]
    
    if not closed_trades:
        return 0.0, 0, 0
    
    winning_trades = [t for t in closed_trades if t.get('pl', 0) > 0]
    total_closed = len(closed_trades)
    wins = len(winning_trades)
    
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0.0
    
    return win_rate, wins, total_closed


def calculate_performance_attribution(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculate performance attribution by strategy and asset."""
    attribution = defaultdict(lambda: {
        'trades': 0,
        'wins': 0,
        'losses': 0,
        'total_pl': 0.0,
        'avg_pl': 0.0,
        'win_rate': 0.0,
        'symbols': defaultdict(lambda: {'trades': 0, 'pl': 0.0})
    })
    
    for trade in trades:
        if trade.get('pl') is None:
            continue
        
        tier = trade.get('tier', 'UNKNOWN')
        symbol = trade.get('symbol', 'UNKNOWN')
        pl = trade.get('pl', 0.0)
        
        attribution[tier]['trades'] += 1
        attribution[tier]['total_pl'] += pl
        attribution[tier]['symbols'][symbol]['trades'] += 1
        attribution[tier]['symbols'][symbol]['pl'] += pl
        
        if pl > 0:
            attribution[tier]['wins'] += 1
        else:
            attribution[tier]['losses'] += 1
    
    # Calculate averages and win rates
    for tier_data in attribution.values():
        if tier_data['trades'] > 0:
            tier_data['avg_pl'] = tier_data['total_pl'] / tier_data['trades']
            tier_data['win_rate'] = (tier_data['wins'] / tier_data['trades'] * 100) if tier_data['trades'] > 0 else 0.0
    
    return dict(attribution)


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
        return "  (Insufficient data - need at least 2 data points)"
    
    equity_array = np.array(equity_curve)
    min_val = np.min(equity_array)
    max_val = np.max(equity_array)
    range_val = max_val - min_val
    
    if range_val == 0:
        return "  (No variation in equity curve)"
    
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


def generate_returns_distribution_chart(returns: List[float], width: int = 50, height: int = 10) -> str:
    """Generate ASCII histogram of returns distribution."""
    if len(returns) < 3:
        return "  (Insufficient data for distribution)"
    
    returns_array = np.array(returns)
    
    # Create bins
    min_ret = np.min(returns_array)
    max_ret = np.max(returns_array)
    bins = np.linspace(min_ret, max_ret, width)
    
    # Count frequencies
    hist, _ = np.histogram(returns_array, bins=bins)
    max_freq = np.max(hist) if len(hist) > 0 else 1
    
    # Normalize to chart height
    normalized = (hist / max_freq * height).astype(int)
    
    # Create chart
    chart_lines = []
    for y in range(height - 1, -1, -1):
        line = "  "
        for freq in normalized:
            line += '█' if freq > y else ' '
        chart_lines.append(line)
    
    # Add labels
    result = f"  {min_ret*100:.2f}% {' ' * (width - 20)} {max_ret*100:.2f}%\n"
    result += '\n'.join(chart_lines)
    
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
        status = '✅' if level < 50 else '⚠️' if level < 75 else '🚨'
        result += f"  {name:20s} [{bar_char * bars:<20}] {level:.1f}% {status}\n"
    
    return result


def generate_risk_alerts(risk_metrics: Dict[str, float], win_rate: float, total_trades: int) -> List[str]:
    """Generate actionable risk alerts."""
    alerts = []
    
    # Drawdown alert
    if risk_metrics.get('max_drawdown_pct', 0.0) > 5.0:
        alerts.append(f"🚨 **Drawdown Alert**: Max drawdown is {risk_metrics.get('max_drawdown_pct', 0.0):.2f}% (threshold: 5%). Consider reducing position sizes.")
    
    # Win rate alert
    if win_rate < 40.0 and total_trades >= 10:
        alerts.append(f"⚠️ **Win Rate Alert**: Win rate is {win_rate:.1f}% (target: >55%). Review strategy logic and entry criteria.")
    
    # Volatility alert
    if risk_metrics.get('volatility', 0.0) > 20.0:
        alerts.append(f"⚠️ **Volatility Alert**: Annualized volatility is {risk_metrics.get('volatility', 0.0):.2f}% (threshold: 20%). Consider diversification.")
    
    # Low trade count alert
    if total_trades < 5:
        alerts.append(f"ℹ️ **Data Alert**: Only {total_trades} trades recorded. Metrics will become more reliable with more trade data.")
    
    # Sharpe ratio alert
    if risk_metrics.get('sharpe_ratio', 0.0) < 0.5 and total_trades >= 10:
        alerts.append(f"⚠️ **Risk-Adjusted Return Alert**: Sharpe ratio is {risk_metrics.get('sharpe_ratio', 0.0):.2f} (target: >1.0). Review risk management.")
    
    return alerts if alerts else ["✅ No critical risk alerts at this time"]


def generate_ai_insights_enhanced(
    trades: List[Dict[str, Any]],
    win_rate: float,
    total_trades: int,
    attribution: Dict[str, Dict[str, Any]],
    risk_metrics: Dict[str, float]
) -> Dict[str, Any]:
    """Generate enhanced AI insights with trade analysis."""
    insights = {
        'summary': '',
        'key_findings': [],
        'recommendations': [],
        'trade_analysis': []
    }
    
    if total_trades == 0:
        insights['summary'] = "No trades executed yet. System is ready for trading."
        insights['key_findings'] = ["Waiting for first trade execution"]
        insights['recommendations'] = ["Monitor system for first trade opportunity"]
        return insights
    
    # Analyze best/worst performing strategies
    best_tier = max(attribution.items(), key=lambda x: x[1].get('total_pl', 0.0), default=(None, {}))
    worst_tier = min(attribution.items(), key=lambda x: x[1].get('total_pl', 0.0), default=(None, {}))
    
    # Generate summary
    if win_rate >= 55:
        insights['summary'] = f"✅ Portfolio is performing well with {win_rate:.1f}% win rate. "
    elif win_rate >= 40:
        insights['summary'] = f"⚠️ Portfolio win rate is {win_rate:.1f}% - below target of 55%. "
    else:
        insights['summary'] = f"🚨 Portfolio win rate is {win_rate:.1f}% - significant improvement needed. "
    
    insights['summary'] += f"Total trades: {total_trades}. "
    
    if best_tier[0]:
        insights['summary'] += f"Best performing strategy: {best_tier[0]} (${best_tier[1].get('total_pl', 0.0):+.2f})."
    
    # Key findings
    if best_tier[0] and best_tier[1].get('total_pl', 0) > 0:
        insights['key_findings'].append(f"✅ {best_tier[0]} is the top performer with ${best_tier[1].get('total_pl', 0.0):+.2f} P/L")
    
    if worst_tier[0] and worst_tier[1].get('total_pl', 0) < 0:
        insights['key_findings'].append(f"⚠️ {worst_tier[0]} is underperforming with ${worst_tier[1].get('total_pl', 0.0):+.2f} P/L")
    
    # Win rate analysis
    if win_rate < 55 and total_trades >= 10:
        insights['key_findings'].append(f"⚠️ Win rate ({win_rate:.1f}%) is below target (55%)")
    
    # Recommendations
    if win_rate < 40 and total_trades >= 10:
        insights['recommendations'].append("Review entry criteria - consider tightening filters")
        insights['recommendations'].append("Analyze losing trades to identify common patterns")
    
    if best_tier[0] and best_tier[1].get('win_rate', 0) > 60:
        insights['recommendations'].append(f"Consider increasing allocation to {best_tier[0]} (win rate: {best_tier[1].get('win_rate', 0):.1f}%)")
    
    if risk_metrics.get('max_drawdown_pct', 0.0) > 5.0:
        insights['recommendations'].append("Reduce position sizes to limit drawdown")
    
    # Trade analysis
    recent_trades = sorted(trades, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]
    for trade in recent_trades:
        symbol = trade.get('symbol', 'UNKNOWN')
        tier = trade.get('tier', 'UNKNOWN')
        pl = trade.get('pl', 0.0)
        status = '✅' if pl > 0 else '❌'
        insights['trade_analysis'].append(f"{status} {symbol} ({tier}): ${pl:+.2f}")
    
    return insights


def generate_world_class_dashboard() -> str:
    """Generate world-class dashboard markdown."""
    
    # Load data
    system_state = load_json_file(DATA_DIR / "system_state.json")
    perf_log = load_json_file(DATA_DIR / "performance_log.json")
    challenge_start = load_json_file(DATA_DIR / "challenge_start.json")
    trades = load_trade_data()
    
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
    
    # Calculate win rate from actual trades
    win_rate, winning_trades, total_closed_trades = calculate_win_rate_from_trades(trades)
    
    # Performance attribution
    attribution = calculate_performance_attribution(trades)
    
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
    
    # Enhanced AI insights
    enhanced_insights = generate_ai_insights_enhanced(
        trades, win_rate, total_closed_trades, attribution, risk_metrics_dict
    )
    
    # Risk alerts
    risk_alerts = generate_risk_alerts(risk_metrics_dict, win_rate, total_closed_trades)
    
    # Performance metrics
    performance = system_state.get('performance', {})
    total_trades = performance.get('total_trades', total_closed_trades)
    
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
    
    # Performance attribution table
    attribution_table = ""
    if attribution:
        attribution_table = "\n| Strategy | Trades | Wins | Losses | Win Rate | Total P/L | Avg P/L |\n"
        attribution_table += "|----------|--------|------|--------|----------|-----------|----------|\n"
        for tier, data in sorted(attribution.items(), key=lambda x: x[1].get('total_pl', 0), reverse=True):
            attribution_table += f"| **{tier}** | {data['trades']} | {data['wins']} | {data['losses']} | {data['win_rate']:.1f}% | ${data['total_pl']:+,.2f} | ${data['avg_pl']:+,.2f} |\n"
    else:
        attribution_table = "  (No trade data available for attribution analysis)"
    
    dashboard = f"""# 🌟 World-Class Trading Dashboard

**Last Updated**: {now.strftime('%Y-%m-%d %I:%M %p ET')}  
**Auto-Updated**: Daily via GitHub Actions  
**Dashboard Version**: World-Class Elite Analytics v2.0

---

## 🎯 North Star Goal

**Target**: **$100+/day profit**

| Metric | Current | Target | Progress |
|--------|---------|--------|----------|
| **Average Daily Profit** | ${avg_daily_profit:.2f}/day | $100.00/day | {display_progress_pct:.2f}% |
| **Total P/L** | ${total_pl:+,.2f} ({total_pl/starting_balance*100:+.2f}%) | TBD | {'✅' if total_pl > 0 else '⚠️'} |
| **Win Rate** | {win_rate:.1f}% ({winning_trades}/{total_closed_trades}) | >55% | {'✅' if win_rate >= 55 else '⚠️' if win_rate >= 40 else '🚨'} |

**Progress Toward $100/Day Goal**: `{north_star_bar}` ({display_progress_pct:.2f}%)  
*This shows how close your average daily profit is to the $100/day target*

---

## 📊 Performance Attribution

### By Strategy

{attribution_table}

### Top Performing Assets

"""
    
    # Add top assets
    asset_performance = defaultdict(lambda: {'trades': 0, 'pl': 0.0, 'wins': 0})
    for trade in trades:
        if trade.get('pl') is None:
            continue
        symbol = trade.get('symbol', 'UNKNOWN')
        asset_performance[symbol]['trades'] += 1
        asset_performance[symbol]['pl'] += trade.get('pl', 0.0)
        if trade.get('pl', 0) > 0:
            asset_performance[symbol]['wins'] += 1
    
    if asset_performance:
        top_assets = sorted(asset_performance.items(), key=lambda x: x[1]['pl'], reverse=True)[:5]
        dashboard += "| Symbol | Trades | Wins | Total P/L | Avg P/L | Win Rate |\n"
        dashboard += "|--------|--------|------|-----------|---------|----------|\n"
        for symbol, data in top_assets:
            win_rate_asset = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0.0
            avg_pl = data['pl'] / data['trades'] if data['trades'] > 0 else 0.0
            dashboard += f"| **{symbol}** | {data['trades']} | {data['wins']} | ${data['pl']:+,.2f} | ${avg_pl:+,.2f} | {win_rate_asset:.1f}% |\n"
    else:
        dashboard += "  (No asset performance data available)\n"
    
    dashboard += f"""
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
| **Max Drawdown** | {risk_metrics_dict.get('max_drawdown_pct', 0.0):.2f}% | {'✅' if risk_metrics_dict.get('max_drawdown_pct', 0.0) < 5.0 else '⚠️' if risk_metrics_dict.get('max_drawdown_pct', 0.0) < 10.0 else '🚨'} |
| **Ulcer Index** | {risk_metrics_dict.get('ulcer_index', 0.0):.2f} | {'✅' if risk_metrics_dict.get('ulcer_index', 0.0) < 5.0 else '⚠️'} |
| **Sharpe Ratio** | {risk_metrics_dict.get('sharpe_ratio', 0.0):.2f} | {'✅' if risk_metrics_dict.get('sharpe_ratio', 0.0) > 1.0 else '⚠️' if risk_metrics_dict.get('sharpe_ratio', 0.0) > 0.5 else '🚨'} |
| **Sortino Ratio** | {risk_metrics_dict.get('sortino_ratio', 0.0):.2f} | {'✅' if risk_metrics_dict.get('sortino_ratio', 0.0) > 1.0 else '⚠️'} |
| **Calmar Ratio** | {risk_metrics_dict.get('calmar_ratio', 0.0):.2f} | {'✅' if risk_metrics_dict.get('calmar_ratio', 0.0) > 1.0 else '⚠️'} |
| **VaR (95%)** | {risk_metrics_dict.get('var_95', 0.0):.2f}% | Risk level |
| **VaR (99%)** | {risk_metrics_dict.get('var_99', 0.0):.2f}% | Extreme risk |
| **CVaR (95%)** | {risk_metrics_dict.get('cvar_95', 0.0):.2f}% | Expected tail loss |
| **Volatility (Annualized)** | {risk_metrics_dict.get('volatility', 0.0):.2f}% | {'✅' if risk_metrics_dict.get('volatility', 0.0) < 20.0 else '⚠️'} |

### Risk Heatmap

{generate_risk_heatmap(risk_metrics_dict)}

### 🚨 Risk Alerts

"""
    
    for alert in risk_alerts:
        dashboard += f"{alert}\n\n"
    
    dashboard += f"""
---

## 🧠 AI-Generated Insights

### Daily Briefing

{enhanced_insights['summary']}

**Key Findings**:
"""
    
    for finding in enhanced_insights['key_findings'][:5]:
        dashboard += f"- {finding}\n"
    
    if not enhanced_insights['key_findings']:
        dashboard += "- No significant findings at this time\n"
    
    dashboard += f"""
**Recommendations**:
"""
    
    for rec in enhanced_insights['recommendations'][:5]:
        dashboard += f"- {rec}\n"
    
    if not enhanced_insights['recommendations']:
        dashboard += "- Continue monitoring current strategy\n"
    
    dashboard += f"""
**Recent Trade Analysis**:
"""
    
    for trade_analysis in enhanced_insights['trade_analysis'][:5]:
        dashboard += f"- {trade_analysis}\n"
    
    if not enhanced_insights['trade_analysis']:
        dashboard += "- No recent trades to analyze\n"
    
    dashboard += f"""
---

## 📈 Equity Curve Visualization

```
{generate_equity_curve_chart(equity_curve) if len(equity_curve) > 1 else '  (Insufficient data for chart - need at least 2 data points)'}
```

"""
    
    if len(returns) > 3:
        dashboard += f"""### Returns Distribution

```
{generate_returns_distribution_chart(returns)}
```

"""
    
    dashboard += f"""
---

## 💰 Financial Performance Summary

| Metric | Value |
|--------|-------|
| **Starting Balance** | ${starting_balance:,.2f} |
| **Current Equity** | ${current_equity:,.2f} |
| **Total P/L** | ${total_pl:+,.2f} ({total_pl/starting_balance*100:+.2f}%) |
| **Total Trades** | {total_trades} |
| **Closed Trades** | {total_closed_trades} |
| **Winning Trades** | {winning_trades} |
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
- [Trade Logs](https://github.com/IgorGanapolsky/trading/tree/main/data/trade_logs)

---

*This world-class dashboard is automatically updated daily by GitHub Actions with elite-level analytics.*  
*Dashboard improvements: Enhanced trade analysis, performance attribution, actionable risk alerts, and better visualizations.*

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
