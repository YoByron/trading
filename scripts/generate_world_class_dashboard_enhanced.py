#!/usr/bin/env python3
"""
Generate World-Class Trading Dashboard (Enhanced Version)

Implements ALL missing features from the critique:
✅ Risk Metrics (Max drawdown, Sharpe, Sortino, VaR, Conditional VaR, Kelly fraction)
✅ Performance Attribution (by symbol, strategy, time-of-day)
✅ Visualizations (equity curve, drawdown, P/L charts)
✅ Real-Time Insights (AI-generated commentary)
✅ Predictive Analytics (Monte Carlo, risk-of-ruin)
✅ Execution Metrics (slippage, fill quality, latency)
✅ Data Completeness Metrics
✅ Benchmark Comparisons (vs S&P 500)
✅ AI Interpretation Layer
"""
import os
import sys
import json
from datetime import datetime, date, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.enhanced_dashboard_metrics import EnhancedMetricsCalculator, load_json_file
from scripts.dashboard_charts import generate_all_charts
from scripts.ai_insights_generator import AIInsightsGenerator

DATA_DIR = Path("data")


def calculate_basic_metrics():
    """Calculate basic metrics for dashboard header."""
    challenge_file = DATA_DIR / "challenge_start.json"
    if challenge_file.exists():
        challenge_data = load_json_file(challenge_file)
        start_date = datetime.fromisoformat(challenge_data["start_date"]).date()
        today = date.today()
        days_elapsed = (today - start_date).days + 1
        starting_balance = challenge_data.get("starting_balance", 100000.0)
    else:
        system_state = load_json_file(DATA_DIR / "system_state.json")
        challenge = system_state.get("challenge", {})
        start_date_str = challenge.get("start_date", "2025-10-29")
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            today = date.today()
            days_elapsed = max((today - start_date).days + 1, 1)
        except:
            days_elapsed = max(
                system_state.get("challenge", {}).get("current_day", 1), 1
            )
        starting_balance = 100000.0

    system_state = load_json_file(DATA_DIR / "system_state.json")
    account = system_state.get("account", {})
    current_equity = account.get("current_equity", starting_balance)
    total_pl = account.get("total_pl", 0.0)
    total_pl_pct = account.get("total_pl_pct", 0.0)

    perf_log = load_json_file(DATA_DIR / "performance_log.json")
    if isinstance(perf_log, list) and perf_log:
        latest_perf = perf_log[-1]
        current_equity = latest_perf.get("equity", current_equity)
        total_pl = latest_perf.get("pl", total_pl)
        total_pl_pct = latest_perf.get("pl_pct", total_pl_pct) * 100

    trading_days = (
        len(perf_log) if isinstance(perf_log, list) and perf_log else days_elapsed
    )
    trading_days = max(trading_days, 1)

    avg_daily_profit = total_pl / trading_days if trading_days > 0 else 0.0
    north_star_target = 100.0
    progress_pct = (
        (avg_daily_profit / north_star_target * 100) if north_star_target > 0 else 0.0
    )

    if total_pl > 0 and progress_pct < 0.01:
        progress_pct = max(0.01, (total_pl / north_star_target) * 100)

    performance = system_state.get("performance", {})
    win_rate = performance.get("win_rate", 0.0) * 100
    total_trades = performance.get("total_trades", 0)

    challenge = system_state.get("challenge", {})
    current_day = challenge.get("current_day", days_elapsed)
    total_days = challenge.get("total_days", 90)
    phase = challenge.get("phase", "R&D Phase - Month 1 (Days 1-30)")

    automation = system_state.get("automation", {})
    automation_status = automation.get("workflow_status", "UNKNOWN")

    today_trades_file = DATA_DIR / f"trades_{date.today().isoformat()}.json"
    today_trades = load_json_file(today_trades_file)
    today_trade_count = len(today_trades) if isinstance(today_trades, list) else 0

    days_remaining = total_days - current_day
    progress_pct_challenge = (current_day / total_days * 100) if total_days > 0 else 0.0

    return {
        "days_elapsed": days_elapsed,
        "current_day": current_day,
        "total_days": total_days,
        "days_remaining": days_remaining,
        "progress_pct_challenge": progress_pct_challenge,
        "phase": phase,
        "starting_balance": starting_balance,
        "current_equity": current_equity,
        "total_pl": total_pl,
        "total_pl_pct": total_pl_pct,
        "avg_daily_profit": avg_daily_profit,
        "north_star_target": north_star_target,
        "progress_pct": progress_pct,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "automation_status": automation_status,
        "today_trade_count": today_trade_count,
    }


def generate_world_class_dashboard() -> str:
    """Generate complete world-class dashboard."""
    # Calculate all metrics
    basic_metrics = calculate_basic_metrics()
    calculator = EnhancedMetricsCalculator(DATA_DIR)
    all_metrics = calculator.calculate_all_metrics()

    # Load data for charts and insights
    perf_log = load_json_file(DATA_DIR / "performance_log.json")
    if not isinstance(perf_log, list):
        perf_log = []

    all_trades = calculator._load_all_trades()

    # Generate charts
    chart_paths = generate_all_charts(perf_log)

    # Generate AI insights
    insights_generator = AIInsightsGenerator()
    ai_insights = insights_generator.generate_daily_insights(
        perf_log,
        all_trades,
        all_metrics.get("risk_metrics", {}),
        all_metrics.get("performance_metrics", {}),
        all_metrics.get("performance_attribution", {}),
    )

    # Extract metrics
    risk = all_metrics.get("risk_metrics", {})
    perf = all_metrics.get("performance_metrics", {})
    enhanced_risk = all_metrics.get("enhanced_risk_metrics", {})
    attribution = all_metrics.get("performance_attribution", {})
    execution = all_metrics.get("execution_metrics", {})
    data_completeness = all_metrics.get("data_completeness", {})
    predictive = all_metrics.get("predictive_analytics", {})
    benchmark = all_metrics.get("benchmark_comparison", {})
    time_analysis = all_metrics.get("time_of_day_analysis", {})
    regime = all_metrics.get("market_regime_classification", {})

    now = datetime.now()

    # Progress bars
    progress_bars = int(basic_metrics["progress_pct_challenge"] / 5)
    progress_bar = "█" * progress_bars + "░" * (20 - progress_bars)

    if basic_metrics["total_pl"] > 0 and basic_metrics["progress_pct"] < 5.0:
        north_star_bars = 1
    else:
        north_star_bars = min(int(basic_metrics["progress_pct"] / 5), 20)
    north_star_bar = "█" * north_star_bars + "░" * (20 - north_star_bars)

    display_progress_pct = (
        max(basic_metrics["progress_pct"], 0.01)
        if basic_metrics["total_pl"] > 0
        else basic_metrics["progress_pct"]
    )

    status_emoji = "✅" if basic_metrics["total_pl"] > 0 else "⚠️"

    # Build dashboard
    dashboard = f"""# 📊 World-Class Trading Dashboard

**Last Updated**: {now.strftime('%Y-%m-%d %I:%M %p ET')}  
**Auto-Updated**: Daily via GitHub Actions  
**Dashboard Version**: Enhanced World-Class (v2.0)

---

## 🎯 North Star Goal

**Target**: **$100+/day profit**

| Metric | Current | Target | Progress |
|--------|---------|--------|----------|
| **Average Daily Profit** | ${basic_metrics['avg_daily_profit']:.2f}/day | $100.00/day | {display_progress_pct:.2f}% |
| **Total P/L** | ${basic_metrics['total_pl']:+,.2f} ({basic_metrics['total_pl_pct']:+.2f}%) | TBD | {status_emoji} |
| **Win Rate** | {basic_metrics['win_rate']:.1f}% | >55% | {'✅' if basic_metrics['win_rate'] >= 55 else '⚠️'} |

**Progress Bar**: `{north_star_bar}` ({display_progress_pct:.2f}%)

**Assessment**: {'✅ **ON TRACK**' if basic_metrics['total_pl'] > 0 and basic_metrics['win_rate'] >= 55 else '⚠️ **R&D PHASE** - Learning, not earning yet'}

---

## 🛡️ Comprehensive Risk Metrics

### Core Risk Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Max Drawdown** | {risk.get('max_drawdown_pct', 0):.2f}% | <10% | {'✅' if risk.get('max_drawdown_pct', 0) < 10 else '⚠️'} |
| **Current Drawdown** | {risk.get('current_drawdown_pct', 0):.2f}% | <5% | {'✅' if risk.get('current_drawdown_pct', 0) < 5 else '⚠️'} |
| **Sharpe Ratio** | {risk.get('sharpe_ratio', 0):.2f} | >1.0 | {'✅' if risk.get('sharpe_ratio', 0) >= 1.0 else '⚠️'} |
| **Sortino Ratio** | {risk.get('sortino_ratio', 0):.2f} | >1.5 | {'✅' if risk.get('sortino_ratio', 0) >= 1.5 else '⚠️'} |
| **Volatility (Annualized)** | {risk.get('volatility_annualized', 0):.2f}% | <20% | {'✅' if risk.get('volatility_annualized', 0) < 20 else '⚠️'} |
| **VaR (95th percentile)** | {risk.get('var_95', 0):.2f}% | >-3% | {'✅' if risk.get('var_95', 0) > -3 else '⚠️'} |
| **Conditional VaR (95th)** | {enhanced_risk.get('conditional_var_95', 0):.2f}% | >-5% | {'✅' if enhanced_risk.get('conditional_var_95', 0) > -5 else '⚠️'} |
| **Kelly Fraction** | {enhanced_risk.get('kelly_fraction', 0):.2f}% | 5-10% | {'✅' if 5 <= enhanced_risk.get('kelly_fraction', 0) <= 10 else '⚠️'} |
| **Margin Usage** | {enhanced_risk.get('margin_usage_pct', 0):.2f}% | <50% | {'✅' if enhanced_risk.get('margin_usage_pct', 0) < 50 else '⚠️'} |
| **Leverage** | {enhanced_risk.get('leverage', 1.0):.2f}x | <2.0x | {'✅' if enhanced_risk.get('leverage', 1.0) < 2.0 else '⚠️'} |

### Risk Exposure by Symbol

| Symbol | Exposure % | P/L | Trades | Win Rate |
|--------|------------|-----|--------|----------|
"""

    # Add symbol attribution
    by_symbol = attribution.get("by_symbol", {})
    if by_symbol:
        for symbol, data in sorted(
            by_symbol.items(), key=lambda x: x[1].get("total_pl", 0), reverse=True
        )[:10]:
            dashboard += f"| {symbol} | {data.get('total_pl', 0)/basic_metrics['current_equity']*100:.2f}% | ${data.get('total_pl', 0):+.2f} | {data.get('trades', 0)} | {data.get('win_rate', 0):.1f}% |\n"
    else:
        dashboard += "| *No symbol data available* | - | - | - | - |\n"

    dashboard += f"""
---

## 📊 Performance Attribution

### By Strategy/Tier

| Strategy | P/L | Trades | Avg P/L per Trade |
|----------|-----|--------|------------------|
"""

    by_strategy = attribution.get("by_strategy", {})
    if by_strategy:
        for strategy, data in sorted(
            by_strategy.items(), key=lambda x: x[1].get("total_pl", 0), reverse=True
        ):
            dashboard += f"| {strategy} | ${data.get('total_pl', 0):+.2f} | {data.get('trades', 0)} | ${data.get('avg_pl_per_trade', 0):+.2f} |\n"
    else:
        dashboard += "| *No strategy data available* | - | - | - |\n"

    dashboard += f"""
### By Time of Day

| Time Period | P/L | Trades | Avg P/L per Trade |
|-------------|-----|--------|------------------|
"""

    by_time = attribution.get("by_time_of_day", {})
    if by_time:
        for time_period, data in by_time.items():
            dashboard += f"| {time_period.capitalize()} | ${data.get('total_pl', 0):+.2f} | {data.get('trades', 0)} | ${data.get('avg_pl_per_trade', 0):+.2f} |\n"
    else:
        dashboard += "| *No time-of-day data available* | - | - | - |\n"

    dashboard += f"""
**Best Trading Time**: {time_analysis.get('best_time', 'N/A')}  
**Worst Trading Time**: {time_analysis.get('worst_time', 'N/A')}

---

## 📈 Visualizations

"""

    # Add chart images
    charts_generated = any(chart_paths.values())
    if charts_generated:
        if chart_paths.get("equity_curve"):
            dashboard += f"### Equity Curve\n\n![Equity Curve]({chart_paths['equity_curve']})\n\n"
        if chart_paths.get("drawdown"):
            dashboard += (
                f"### Drawdown Chart\n\n![Drawdown]({chart_paths['drawdown']})\n\n"
            )
        if chart_paths.get("daily_pl"):
            dashboard += f"### Daily P/L Distribution\n\n![Daily P/L]({chart_paths['daily_pl']})\n\n"
        if chart_paths.get("rolling_sharpe_7d"):
            dashboard += f"### Rolling Sharpe Ratio (7-Day)\n\n![Rolling Sharpe]({chart_paths['rolling_sharpe_7d']})\n\n"
    else:
        # Show helpful message when charts can't be generated
        perf_log_count = len(perf_log) if isinstance(perf_log, list) else 0
        dashboard += f"### Equity Curve Visualization\n\n"
        if perf_log_count < 2:
            dashboard += f"*Insufficient data for chart (need at least 2 data points, have {perf_log_count})*\n\n"
        else:
            dashboard += f"*Charts will be generated when matplotlib is available in the environment. Data available: {perf_log_count} data points.*\n\n"

    dashboard += f"""
---

## ⚡ Execution Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Avg Slippage** | {execution.get('avg_slippage', 0):.3f}% | <0.5% | {'✅' if execution.get('avg_slippage', 0) < 0.5 else '⚠️'} |
| **Fill Quality** | {execution.get('fill_quality', 0):.1f}/100 | >90 | {'✅' if execution.get('fill_quality', 0) > 90 else '⚠️'} |
| **Order Success Rate** | {execution.get('order_success_rate', 0):.1f}% | >95% | {'✅' if execution.get('order_success_rate', 0) > 95 else '⚠️'} |
| **Order Reject Rate** | {execution.get('order_reject_rate', 0):.1f}% | <5% | {'✅' if execution.get('order_reject_rate', 0) < 5 else '⚠️'} |
| **Avg Fill Time** | {execution.get('avg_fill_time_ms', 0):.0f} ms | <200ms | {'✅' if execution.get('avg_fill_time_ms', 0) < 200 else '⚠️'} |
| **Broker Latency** | {execution.get('broker_latency_ms', 0):.0f} ms | <100ms | {'✅' if execution.get('broker_latency_ms', 0) < 100 else '⚠️'} |

---

## 📊 Data Completeness & Quality

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Performance Log Completeness** | {data_completeness.get('performance_log_completeness', 0):.1f}% | >95% | {'✅' if data_completeness.get('performance_log_completeness', 0) > 95 else '⚠️'} |
| **Missing Dates** | {data_completeness.get('missing_dates_count', 0)} | 0 | {'✅' if data_completeness.get('missing_dates_count', 0) == 0 else '⚠️'} |
| **Data Freshness** | {data_completeness.get('data_freshness_days', 999)} days old | <1 day | {'✅' if data_completeness.get('data_freshness_days', 999) < 1 else '⚠️'} |
| **Missing Candle %** | {data_completeness.get('missing_candle_pct', 0):.2f}% | <1% | {'✅' if data_completeness.get('missing_candle_pct', 0) < 1 else '⚠️'} |
| **Data Sources** | {', '.join(data_completeness.get('data_sources_used', []))} | Multiple | {'✅' if len(data_completeness.get('data_sources_used', [])) > 1 else '⚠️'} |
| **Model Version** | {data_completeness.get('model_version', '1.0')} | Latest | ✅ |

---

## 🔮 Predictive Analytics

### Monte Carlo Forecast (30-Day)

| Metric | Value |
|--------|-------|
| **Expected P/L (30d)** | ${predictive.get('expected_pl_30d', 0):+.2f} |
| **Forecast Mean** | ${predictive.get('monte_carlo_forecast', {}).get('mean_30d', 0):,.2f} |
| **Forecast Std Dev** | ${predictive.get('monte_carlo_forecast', {}).get('std_30d', 0):,.2f} |
| **5th Percentile** | ${predictive.get('monte_carlo_forecast', {}).get('percentile_5', 0):,.2f} |
| **95th Percentile** | ${predictive.get('monte_carlo_forecast', {}).get('percentile_95', 0):,.2f} |
| **Risk of Ruin** | {predictive.get('risk_of_ruin', 0):.2f}% | {'✅' if predictive.get('risk_of_ruin', 0) < 5 else '⚠️'} |
| **Forecasted Drawdown** | {predictive.get('forecasted_drawdown', 0):.2f}% |
| **Strategy Decay Detected** | {'⚠️ YES' if predictive.get('strategy_decay_detected', False) else '✅ NO'} |

---

## 📊 Benchmark Comparison (vs S&P 500)

| Metric | Portfolio | Benchmark | Difference | Status |
|--------|-----------|-----------|------------|--------|
| **Total Return** | {benchmark.get('portfolio_return', 0):+.2f}% | {benchmark.get('benchmark_return', 0):+.2f}% | {benchmark.get('alpha', 0):+.2f}% | {'✅ Outperforming' if benchmark.get('alpha', 0) > 0 else '⚠️ Underperforming'} |
| **Alpha** | {benchmark.get('alpha', 0):+.2f}% | - | - | {'✅ Positive Alpha' if benchmark.get('alpha', 0) > 0 else '⚠️ Negative Alpha'} |
| **Beta** | {benchmark.get('beta', 1.0):.2f} | 1.0 | {benchmark.get('beta', 1.0) - 1.0:+.2f} | {'Higher Risk' if benchmark.get('beta', 1.0) > 1.0 else 'Lower Risk'} |
| **Data Available** | {'✅ Yes' if benchmark.get('data_available', False) else '⚠️ Limited'} | - | - | - |

---

## 🤖 AI-Generated Insights

### Daily Summary

{ai_insights.get('summary', 'No summary available.')}

### Strategy Health Score

**{ai_insights.get('strategy_health', {}).get('emoji', '❓')} {ai_insights.get('strategy_health', {}).get('status', 'UNKNOWN')}** ({ai_insights.get('strategy_health', {}).get('score', 0):.0f}/100)

"""

    # Add health factors
    health_factors = ai_insights.get("strategy_health", {}).get("factors", [])
    if health_factors:
        dashboard += "\n**Health Factors:**\n"
        for factor in health_factors:
            dashboard += f"- {factor}\n"

    dashboard += f"""
### Trade Analysis

"""

    trade_analysis = ai_insights.get("trade_analysis", [])
    if trade_analysis:
        for analysis in trade_analysis:
            dashboard += f"{analysis}\n\n"
    else:
        dashboard += "No trade analysis available.\n\n"

    dashboard += f"""
### Anomalies Detected

"""

    anomalies = ai_insights.get("anomalies", [])
    if anomalies:
        for anomaly in anomalies:
            dashboard += f"{anomaly}\n\n"
    else:
        dashboard += "✅ No anomalies detected.\n\n"

    regime_shift = ai_insights.get("regime_shift")
    if regime_shift:
        dashboard += f"### Market Regime Shift\n\n{regime_shift}\n\n"

    dashboard += f"""
### Recommendations

"""

    recommendations = ai_insights.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            dashboard += f"{rec}\n\n"
    else:
        dashboard += "✅ No recommendations at this time.\n\n"

    dashboard += f"""
---

## 📈 Market Regime Classification

| Metric | Value |
|--------|-------|
| **Current Regime** | {regime.get('regime', 'UNKNOWN')} |
| **Regime Type** | {regime.get('regime_type', 'UNKNOWN')} |
| **Confidence** | {regime.get('confidence', 0):.1f}/1.0 |
| **Trend Strength** | {regime.get('trend_strength', 0):.2f} |
| **Volatility Regime** | {regime.get('volatility_regime', 'NORMAL')} |
| **Avg Daily Return** | {regime.get('avg_daily_return', 0):+.2f}% |
| **Volatility** | {regime.get('volatility', 0):.2f}% |

---

## 💰 Financial Performance Summary

| Metric | Value |
|--------|-------|
| **Starting Balance** | ${basic_metrics['starting_balance']:,.2f} |
| **Current Equity** | ${basic_metrics['current_equity']:,.2f} |
| **Total P/L** | ${basic_metrics['total_pl']:+,.2f} ({basic_metrics['total_pl_pct']:+.2f}%) |
| **Average Daily Profit** | ${basic_metrics['avg_daily_profit']:+.2f} |
| **Total Trades** | {basic_metrics['total_trades']} |
| **Win Rate** | {basic_metrics['win_rate']:.1f}% |
| **Trades Today** | {basic_metrics['today_trade_count']} |

---

## 📈 90-Day R&D Challenge Progress

**Current**: Day {basic_metrics['current_day']} of {basic_metrics['total_days']} ({basic_metrics['progress_pct_challenge']:.1f}% complete)  
**Phase**: {basic_metrics['phase']}  
**Days Remaining**: {basic_metrics['days_remaining']}

**Progress Bar**: `{progress_bar}` ({basic_metrics['progress_pct_challenge']:.1f}%)

---

## 🚨 Risk Guardrails & Safety

| Guardrail | Current | Limit | Status |
|-----------|---------|-------|--------|
| **Max Drawdown** | {risk.get('max_drawdown_pct', 0):.2f}% | <10% | {'✅' if risk.get('max_drawdown_pct', 0) < 10 else '⚠️'} |
| **Sharpe Ratio** | {risk.get('sharpe_ratio', 0):.2f} | >1.0 | {'✅' if risk.get('sharpe_ratio', 0) >= 1.0 else '⚠️'} |
| **Volatility** | {risk.get('volatility_annualized', 0):.2f}% | <20% | {'✅' if risk.get('volatility_annualized', 0) < 20 else '⚠️'} |

---

## 📝 Notes

**Dashboard Features**:
- ✅ Comprehensive risk metrics (Sharpe, Sortino, VaR, Conditional VaR, Kelly fraction)
- ✅ Performance attribution by symbol, strategy, and time-of-day
- ✅ Visualizations (equity curve, drawdown, P/L charts)
- ✅ AI-generated insights and recommendations
- ✅ Predictive analytics (Monte Carlo forecasting, risk-of-ruin)
- ✅ Execution metrics (slippage, fill quality, latency)
- ✅ Data completeness tracking
- ✅ Benchmark comparison vs S&P 500
- ✅ Market regime classification

"""

    # Determine active strategy
    is_crypto_mode = False
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        log_files = [
            Path("logs/trading_system.log"),
            Path("logs/launchd_stdout.log"),
            Path("logs/launchd_stderr.log"),
        ]

        for log_file in log_files:
            if log_file.exists():
                # Check last 1000 lines for today's execution mode
                with open(log_file, "r") as f:
                    try:
                        lines = f.readlines()[-1000:]
                        for line in lines:
                            if (
                                today_str in line
                                and "CRYPTO STRATEGY - Daily Execution" in line
                            ):
                                is_crypto_mode = True
                                break
                    except Exception:
                        continue
            if is_crypto_mode:
                break
    except Exception:
        pass

    dashboard += f"""
**Current Strategy**: 
"""
    if is_crypto_mode:
        dashboard += "- **MODE**: 🌐 CRYPTO (Weekend/Holiday)\n"
        dashboard += "- **Strategy**: Tier 5 - Cryptocurrency 24/7 (BTC/ETH)\n"
        dashboard += "- **Allocation**: $10/day fixed (Crypto only)\n"
        dashboard += "- **Status**: ✅ Active (Monitoring BTC/ETH)\n"
    else:
        dashboard += "- **MODE**: 📈 STANDARD (Weekday)\n"
        dashboard += "- **Strategy**: Momentum (MACD + RSI + Volume)\n"
        dashboard += "- **Allocation**: 70% Core ETFs (SPY/QQQ/VOO), 30% Growth (NVDA/GOOGL/AMZN)\n"
        dashboard += "- **Daily Investment**: $10/day fixed\n"

    dashboard += f"""
---

## 💰 Options Income (Yield Generation)

"""
    # Check for options activity in logs
    options_activity = []
    try:
        log_files = [Path("logs/trading_system.log")]
        for log_file in log_files:
            if log_file.exists():
                with open(log_file, "r") as f:
                    lines = f.readlines()[-2000:]  # Check last 2000 lines
                    for line in lines:
                        if "EXECUTING OPTIONS STRATEGY" in line:
                            options_activity = []  # Reset on new execution start
                        if "Proposed: Sell" in line:
                            parts = line.split("Proposed: Sell ")[1].strip()
                            options_activity.append(
                                f"- 🎯 **Opportunity**: Sell {parts}"
                            )
                        if "Options Strategy: No opportunities found" in line:
                            options_activity = [
                                "- ℹ️ No covered call opportunities found today (need 100+ shares)"
                            ]
    except Exception:
        pass

    if options_activity:
        for activity in options_activity[-5:]:  # Show last 5
            dashboard += f"{activity}\n"
    else:
        dashboard += "- ℹ️ Strategy active (Monitoring for 100+ share positions)\n"

    dashboard += f"""
---

## 🤖 AI & ML System Status


### RL Training Status
"""

    # Add RL training status
    training_status_file = DATA_DIR / "training_status.json"
    if training_status_file.exists():
        try:
            training_status = load_json_file(training_status_file)
            cloud_jobs = training_status.get("cloud_jobs", {})
            last_training = training_status.get("last_training", {})

            active_jobs = sum(
                1
                for j in cloud_jobs.values()
                if j.get("status") in ["submitted", "running", "in_progress"]
            )
            completed_jobs = sum(
                1
                for j in cloud_jobs.values()
                if j.get("status") in ["completed", "success"]
            )

            dashboard += f"| **Cloud RL Jobs** | {len(cloud_jobs)} total ({active_jobs} active, {completed_jobs} completed) |\n"
            dashboard += (
                f"| **Last Training** | {len(last_training)} symbols trained |\n"
            )

            # Show recent training times
            if last_training:
                recent_symbols = list(last_training.items())[:5]
                dashboard += f"| **Recent Training** | {', '.join([f'{s}' for s, _ in recent_symbols])} |\n"

            # Add Vertex AI console link
            dashboard += f"| **Vertex AI Console** | [View Jobs →](https://console.cloud.google.com/vertex-ai/training/custom-jobs?project=email-outreach-ai-460404) |\n"
        except Exception as e:
            dashboard += (
                f"| **Status** | ⚠️ Unable to load training status ({str(e)[:50]}) |\n"
            )
    else:
        dashboard += "| **Status** | ⚠️ No training data available |\n"
        dashboard += "| **Vertex AI Console** | [View Jobs →](https://console.cloud.google.com/vertex-ai/training/custom-jobs?project=email-outreach-ai-460404) |\n"

    dashboard += """
### LangSmith Monitoring
"""

    # LangSmith Project ID
    project_id = "04fa554e-f155-4039-bb7f-e866f082103b"
    project_url = f"https://smith.langchain.com/o/default/projects/p/{project_id}"

    # Check LangSmith status
    try:
        sys.path.insert(
            0,
            str(
                Path(__file__).parent.parent
                / ".claude"
                / "skills"
                / "langsmith_monitor"
                / "scripts"
            ),
        )
        from langsmith_monitor import LangSmithMonitor

        monitor = LangSmithMonitor()
        health = monitor.monitor_health()

        if health.get("success"):
            stats = monitor.get_project_stats("trading-rl-training", days=7)
            if stats.get("success"):
                dashboard += f"| **Status** | ✅ Healthy |\n"
                dashboard += f"| **Total Runs** (7d) | {stats.get('total_runs', 0)} |\n"
                dashboard += (
                    f"| **Success Rate** | {stats.get('success_rate', 0):.1f}% |\n"
                )
                dashboard += f"| **Avg Duration** | {stats.get('average_duration_seconds', 0):.1f}s |\n"
                dashboard += f"| **Project Dashboard** | [trading-rl-training →]({project_url}) |\n"
            else:
                dashboard += f"| **Status** | ✅ Healthy (no stats available) |\n"
                dashboard += f"| **Project Dashboard** | [trading-rl-training →]({project_url}) |\n"
        else:
            dashboard += f"| **Status** | ⚠️ {health.get('error', 'Unknown error')} |\n"
            dashboard += (
                f"| **Project Dashboard** | [trading-rl-training →]({project_url}) |\n"
            )
    except Exception as e:
        dashboard += "| **Status** | ⚠️ LangSmith monitor unavailable |\n"
        dashboard += (
            f"| **Project Dashboard** | [trading-rl-training →]({project_url}) |\n"
        )

    dashboard += r"""
---

## 🌐 External Dashboards & Monitoring

### LangSmith Observability
- **[LangSmith Dashboard](https://smith.langchain.com)** - Main dashboard
"""
    dashboard += f"- **[Trading RL Training Project]({project_url})** - RL training runs and traces\n"
    dashboard += f"  *Project ID: `{project_id}`*\n"
    dashboard += r"""- **[All Projects](https://smith.langchain.com/o/default/projects)** - View all LangSmith projects


### Vertex AI Cloud RL
- **[Vertex AI Console](https://console.cloud.google.com/vertex-ai?project=email-outreach-ai-460404)** - Main Vertex AI dashboard
- **[Training Jobs](https://console.cloud.google.com/vertex-ai/training/custom-jobs?project=email-outreach-ai-460404)** - View RL training jobs
- **[Models](https://console.cloud.google.com/vertex-ai/models?project=email-outreach-ai-460404)** - Trained models
- **[Experiments](https://console.cloud.google.com/vertex-ai/experiments?project=email-outreach-ai-460404)** - Training experiments

**Project**: `email-outreach-ai-460404` | **Location**: `us-central1`

---

*This dashboard is automatically updated daily by GitHub Actions after trading execution.*  
*World-class metrics powered by comprehensive risk & performance analytics.*
"""

    return dashboard


def main():
    """Generate and save enhanced dashboard."""
    dashboard = generate_world_class_dashboard()

    output_file = Path("wiki/Progress-Dashboard.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write(dashboard)

    print("✅ Enhanced world-class progress dashboard generated successfully!")
    print(f"📄 Saved to: {output_file}")
    print(
        "🎯 Features: Risk metrics, Attribution, Visualizations, AI Insights, Predictive Analytics"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
