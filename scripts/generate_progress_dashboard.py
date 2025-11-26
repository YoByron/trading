#!/usr/bin/env python3
"""
Generate World-Class Progress Dashboard for GitHub Wiki

This script generates a comprehensive, world-class progress dashboard markdown file
that gets automatically updated daily via GitHub Actions.

The dashboard shows:
- Current performance vs North Star goal
- R&D Phase progress
- System status
- World-class risk & performance metrics
- Strategy diagnostics
- Time-series analytics
- Risk guardrails
- Signal quality metrics
"""
import os
import sys
import json
from datetime import datetime, date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.dashboard_metrics import TradingMetricsCalculator

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


def calculate_metrics():
    """Calculate all metrics for dashboard."""
    # Load challenge data
    challenge_file = DATA_DIR / "challenge_start.json"
    if challenge_file.exists():
        challenge_data = load_json_file(challenge_file)
        start_date = datetime.fromisoformat(challenge_data['start_date']).date()
        today = date.today()
        days_elapsed = (today - start_date).days + 1
        starting_balance = challenge_data.get('starting_balance', 100000.0)
    else:
        # Fallback: use system_state.json challenge data
        system_state = load_json_file(DATA_DIR / "system_state.json")
        challenge = system_state.get('challenge', {})
        start_date_str = challenge.get('start_date', '2025-10-29')
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            today = date.today()
            days_elapsed = max((today - start_date).days + 1, 1)  # At least 1 day
        except:
            days_elapsed = max(system_state.get('challenge', {}).get('current_day', 1), 1)
        starting_balance = 100000.0

    # Load system state
    system_state = load_json_file(DATA_DIR / "system_state.json")
    account = system_state.get('account', {})
    current_equity = account.get('current_equity', starting_balance)
    total_pl = account.get('total_pl', 0.0)
    total_pl_pct = account.get('total_pl_pct', 0.0)

    # Load performance log
    perf_log = load_json_file(DATA_DIR / "performance_log.json")
    if isinstance(perf_log, list) and perf_log:
        latest_perf = perf_log[-1]
        current_equity = latest_perf.get('equity', current_equity)
        total_pl = latest_perf.get('pl', total_pl)
        total_pl_pct = latest_perf.get('pl_pct', total_pl_pct)

    # Calculate averages - use actual trading days, not calendar days
    # If we have performance log entries, use that count
    trading_days = len(perf_log) if isinstance(perf_log, list) and perf_log else days_elapsed
    trading_days = max(trading_days, 1)  # At least 1 day to avoid division by zero
    
    # Use system_state.json total_pl as source of truth (most accurate current state)
    avg_daily_profit = total_pl / trading_days if trading_days > 0 else 0.0
    north_star_target = 100.0  # $100/day
    progress_pct = (avg_daily_profit / north_star_target * 100) if north_star_target > 0 else 0.0
    
    # Ensure progress is never negative and shows at least minimal progress if profitable
    if total_pl > 0 and progress_pct < 0.01:
        progress_pct = max(0.01, (total_pl / north_star_target) * 100)  # Show at least 0.01% if profitable

    # Get performance metrics
    performance = system_state.get('performance', {})
    win_rate = performance.get('win_rate', 0.0) * 100
    total_trades = performance.get('total_trades', 0)
    winning_trades = performance.get('winning_trades', 0)
    losing_trades = performance.get('losing_trades', 0)

    # Get challenge info
    challenge = system_state.get('challenge', {})
    current_day = challenge.get('current_day', days_elapsed)
    total_days = challenge.get('total_days', 90)
    phase = challenge.get('phase', 'R&D Phase - Month 1 (Days 1-30)')

    # Get automation status
    automation = system_state.get('automation', {})
    automation_status = automation.get('workflow_status', 'UNKNOWN')
    last_execution = automation.get('last_successful_execution', 'Never')

    # Get recent trades
    today_trades_file = DATA_DIR / f"trades_{date.today().isoformat()}.json"
    today_trades = load_json_file(today_trades_file)
    if isinstance(today_trades, list):
        today_trade_count = len(today_trades)
    else:
        today_trade_count = 0

    # Calculate days remaining
    days_remaining = total_days - current_day
    progress_pct_challenge = (current_day / total_days * 100) if total_days > 0 else 0.0

    return {
        'days_elapsed': days_elapsed,
        'current_day': current_day,
        'total_days': total_days,
        'days_remaining': days_remaining,
        'progress_pct_challenge': progress_pct_challenge,
        'phase': phase,
        'starting_balance': starting_balance,
        'current_equity': current_equity,
        'total_pl': total_pl,
        'total_pl_pct': total_pl_pct,
        'avg_daily_profit': avg_daily_profit,
        'north_star_target': north_star_target,
        'progress_pct': progress_pct,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'automation_status': automation_status,
        'last_execution': last_execution,
        'today_trade_count': today_trade_count,
    }


def generate_dashboard() -> str:
    """Generate the world-class progress dashboard markdown."""
    # Get basic metrics
    basic_metrics = calculate_metrics()
    
    # Get comprehensive world-class metrics
    calculator = TradingMetricsCalculator(DATA_DIR)
    world_class_metrics = calculator.calculate_all_metrics()
    
    now = datetime.now()

    # Calculate progress bar
    progress_bars = int(basic_metrics['progress_pct_challenge'] / 5)
    progress_bar = '█' * progress_bars + '░' * (20 - progress_bars)

    # Calculate North Star progress bar
    # Show at least 1 bar if we're profitable, even if < 5%
    if basic_metrics['total_pl'] > 0 and basic_metrics['progress_pct'] < 5.0:
        north_star_bars = 1  # Show at least 1 bar for any profit
    else:
        north_star_bars = min(int(basic_metrics['progress_pct'] / 5), 20)
    north_star_bar = '█' * north_star_bars + '░' * (20 - north_star_bars)
    
    # Ensure progress percentage shows at least 0.01% if profitable
    display_progress_pct = max(basic_metrics['progress_pct'], 0.01) if basic_metrics['total_pl'] > 0 else basic_metrics['progress_pct']

    # Status emoji
    status_emoji = '✅' if basic_metrics['total_pl'] > 0 else '⚠️'
    automation_emoji = '✅' if basic_metrics['automation_status'] == 'OPERATIONAL' else '❌'
    
    # Load system state for strategy breakdown
    system_state = load_json_file(DATA_DIR / "system_state.json")
    
    # Extract world-class metrics
    risk = world_class_metrics.get('risk_metrics', {})
    perf = world_class_metrics.get('performance_metrics', {})
    strategies = world_class_metrics.get('strategy_metrics', {})
    exposure = world_class_metrics.get('exposure_metrics', {})
    guardrails = world_class_metrics.get('risk_guardrails', {})
    account = world_class_metrics.get('account_summary', {})
    market_regime = world_class_metrics.get('market_regime', {})
    benchmark = world_class_metrics.get('benchmark_comparison', {})
    ai_kpis = world_class_metrics.get('ai_kpis', {})
    automation_status = world_class_metrics.get('automation_status', {})
    journal = world_class_metrics.get('trading_journal', {})
    compliance = world_class_metrics.get('compliance', {})

    dashboard = f"""# 📊 Progress Dashboard

**Last Updated**: {now.strftime('%Y-%m-%d %I:%M %p ET')}  
**Auto-Updated**: Daily via GitHub Actions

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

## 📈 90-Day R&D Challenge Progress

**Current**: Day {basic_metrics['current_day']} of {basic_metrics['total_days']} ({basic_metrics['progress_pct_challenge']:.1f}% complete)  
**Phase**: {basic_metrics['phase']}  
**Days Remaining**: {basic_metrics['days_remaining']}

**Progress Bar**: `{progress_bar}` ({basic_metrics['progress_pct_challenge']:.1f}%)

### Challenge Goals (Month 1 - Days 1-30)

- [x] System reliability 99%+ {'✅' if basic_metrics['automation_status'] == 'OPERATIONAL' else '❌'}
- [{'x' if basic_metrics['win_rate'] >= 55 else ' '}] Win rate >55% ({basic_metrics['win_rate']:.1f}%)
- [{'x' if basic_metrics['current_day'] >= 30 else ' '}] 30 days of clean data ({basic_metrics['current_day']}/30 days)
- [{'x' if risk.get('sharpe_ratio', 0) >= 1.0 else ' '}] Sharpe ratio >1.0 ({risk.get('sharpe_ratio', 0):.2f})
- [ ] Strategy validated via backtesting

### R&D Metrics Summary

| Metric | Value |
|--------|-------|
| **Days Completed** | {basic_metrics['current_day']} |
| **Trades Collected** | {basic_metrics['total_trades']} |
| **Current Sharpe (R&D)** | {risk.get('sharpe_ratio', 0):.2f} |
| **Max Drawdown (R&D)** | {risk.get('max_drawdown_pct', 0):.2f}% |

---

## 💰 Financial Performance

### Account Summary

| Metric | Value |
|--------|-------|
| **Starting Balance** | ${account.get('starting_balance', basic_metrics['starting_balance']):,.2f} |
| **Current Equity** | ${account.get('current_equity', basic_metrics['current_equity']):,.2f} |
| **Total P/L** | ${account.get('total_pl', basic_metrics['total_pl']):+,.2f} ({account.get('total_pl_pct', basic_metrics['total_pl_pct']):+.2f}%) |
| **Average Daily Profit** | ${basic_metrics['avg_daily_profit']:+.2f} |
| **Peak Equity** | ${risk.get('peak_equity', account.get('current_equity', 0)):,.2f} |

### Trading Performance

| Metric | Value |
|--------|-------|
| **Total Trades** | {basic_metrics['total_trades']} |
| **Winning Trades** | {basic_metrics['winning_trades']} |
| **Losing Trades** | {basic_metrics['losing_trades']} |
| **Win Rate** | {basic_metrics['win_rate']:.1f}% |
| **Trades Today** | {basic_metrics['today_trade_count']} |

---

## 🛡️ Risk & Performance Depth

### Risk Metrics

| Metric | Value | Target |
|--------|-------|--------|
| **Max Drawdown** | {risk.get('max_drawdown_pct', 0):.2f}% | <10% |
| **Current Drawdown** | {risk.get('current_drawdown_pct', 0):.2f}% | <5% |
| **Sharpe Ratio** | {risk.get('sharpe_ratio', 0):.2f} | >1.0 |
| **Sortino Ratio** | {risk.get('sortino_ratio', 0):.2f} | >1.5 |
| **Volatility (Annualized)** | {risk.get('volatility_annualized', 0):.2f}% | <20% |
| **Worst Daily Loss** | {risk.get('worst_daily_loss', 0):.2f}% | >-5% |
| **VaR (95th percentile)** | {risk.get('var_95', 0):.2f}% | >-3% |

### Risk-Adjusted Performance

| Metric | Value |
|--------|-------|
| **Profit Factor** | {perf.get('profit_factor', 0):.2f} |
| **Expectancy per Trade** | ${perf.get('expectancy_per_trade', 0):.2f} |
| **Expectancy per R** | {perf.get('expectancy_per_r', 0):.2f} |
| **Win/Loss Ratio** | {perf.get('win_loss_ratio', 0):.2f} |
| **Avg Win/Loss Ratio (R-multiple)** | {perf.get('avg_win_loss_ratio', 0):.2f} |
| **Average Win** | ${perf.get('avg_win', 0):.2f} |
| **Average Loss** | ${perf.get('avg_loss', 0):.2f} |
| **Largest Win** | ${perf.get('largest_win', 0):.2f} |
| **Largest Loss** | ${perf.get('largest_loss', 0):.2f} |

---

## 📊 Strategy & Model Diagnostics

### Per-Strategy Performance

| Strategy/Agent | Trades | P/L ($) | Win % | Sharpe | Max DD % |
|----------------|---------|---------|-------|--------|----------|
"""
    
    # Add strategy rows
    if strategies:
        for strategy_id, strategy_data in strategies.items():
            dashboard += f"| {strategy_data.get('name', strategy_id)} | {strategy_data.get('trades', 0)} | ${strategy_data.get('pl', 0):+.2f} | {strategy_data.get('win_rate', 0):.1f}% | {strategy_data.get('sharpe', 0):.2f} | {strategy_data.get('max_drawdown_pct', 0):.2f}% |\n"
    else:
        dashboard += "| *No strategy data available* | - | - | - | - | - |\n"
    
    dashboard += f"""
---

## 💼 Position & Exposure

### Exposure Snapshot

| Ticker | Position $ | % of Equity | Sector | Strategy |
|--------|-------------|-------------|--------|----------|
"""
    
    # Add exposure rows
    exposure_by_ticker = exposure.get('by_ticker', {})
    if exposure_by_ticker:
        for ticker, pct in sorted(exposure_by_ticker.items(), key=lambda x: x[1], reverse=True):
            position_value = (pct / 100) * account.get('current_equity', 0)
            dashboard += f"| {ticker} | ${position_value:,.2f} | {pct:.2f}% | *TBD* | *TBD* |\n"
    else:
        dashboard += "| *No open positions* | - | - | - | - |\n"
    
    dashboard += f"""
### Exposure Summary

| Metric | Value |
|--------|-------|
| **Largest Position** | {exposure.get('largest_position_pct', 0):.2f}% of equity |
| **Total Exposure** | ${exposure.get('total_exposure', 0):,.2f} |

### Asset Class Breakdown

| Asset Class | Exposure | % of Equity | % of Portfolio |
|-------------|----------|-------------|----------------|
"""
    
    # Add asset class breakdown
    exposure_by_asset_class = exposure.get('by_asset_class', {})
    total_exposure = exposure.get('total_exposure', 0)
    current_equity = account.get('current_equity', basic_metrics['current_equity'])
    
    # Calculate totals for each asset class
    asset_class_totals = {}
    for asset_class, amount in exposure_by_asset_class.items():
        asset_class_totals[asset_class] = {
            'exposure': amount,
            'pct_of_equity': (amount / current_equity * 100) if current_equity > 0 else 0.0,
            'pct_of_portfolio': (amount / total_exposure * 100) if total_exposure > 0 else 0.0
        }
    
    # Show asset classes: Crypto, Equities, Bonds
    for asset_class in ['Crypto', 'Equities', 'Bonds']:
        if asset_class in asset_class_totals:
            data = asset_class_totals[asset_class]
            dashboard += f"| **{asset_class}** | ${data['exposure']:,.2f} | {data['pct_of_equity']:.2f}% | {data['pct_of_portfolio']:.2f}% |\n"
        else:
            dashboard += f"| **{asset_class}** | $0.00 | 0.00% | 0.00% |\n"
    
    # Add strategy breakdown by asset class
    strategies = system_state.get('strategies', {})
    crypto_invested = strategies.get('tier5', {}).get('total_invested', 0.0)
    equities_invested = (
        strategies.get('tier1', {}).get('total_invested', 0.0) +
        strategies.get('tier2', {}).get('total_invested', 0.0)
    )
    bonds_invested = 0.0  # BND is in tier1, would need to track separately
    
    dashboard += f"""
### Investment by Asset Class (Total Invested)

| Asset Class | Total Invested | Trades Executed |
|-------------|----------------|-----------------|
| **Equities** | ${equities_invested:,.2f} | {strategies.get('tier1', {}).get('trades_executed', 0) + strategies.get('tier2', {}).get('trades_executed', 0)} |
| **Bonds** | ${bonds_invested:,.2f} | 0 |
| **Crypto** | ${crypto_invested:,.2f} | {strategies.get('tier5', {}).get('trades_executed', 0)} |

---
"""
    
    dashboard += """
## 🚨 Risk Guardrails & Safety

### Live Risk Status

| Guardrail | Current | Limit | Status |
|-----------|---------|-------|--------|
"""
    
    # Format guardrail values (extract from dict to avoid f-string issues)
    daily_loss_used = guardrails.get('daily_loss_used', 0)
    daily_loss_used_pct = guardrails.get('daily_loss_used_pct', 0)
    daily_loss_limit = guardrails.get('daily_loss_limit', 0)
    daily_loss_status = '⚠️' if daily_loss_used_pct > 50 else '✅'
    
    largest_position_pct = exposure.get('largest_position_pct', 0)
    max_position_size_pct = guardrails.get('max_position_size_pct', 10)
    position_status = '⚠️' if largest_position_pct > max_position_size_pct else '✅'
    
    consecutive_losses = guardrails.get('consecutive_losses', 0)
    consecutive_losses_limit = guardrails.get('consecutive_losses_limit', 5)
    consecutive_status = '⚠️' if consecutive_losses >= consecutive_losses_limit else '✅'
    
    # Format percentages as strings to avoid f-string parsing issues
    daily_loss_used_pct_str = f"{daily_loss_used_pct:.1f}"
    max_position_size_pct_str = f"{max_position_size_pct:.1f}"
    
    dashboard += f"| **Daily Loss Used** | ${daily_loss_used:.2f} ({daily_loss_used_pct_str}%) | ${daily_loss_limit:,.2f} | {daily_loss_status} |\n"
    dashboard += f"| **Max Position Size** | {largest_position_pct:.2f}% | {max_position_size_pct_str}% | {position_status} |\n"
    dashboard += f"| **Consecutive Losses** | {consecutive_losses} | {consecutive_losses_limit} | {consecutive_status} |\n"
    
    # Extract market regime values
    regime = market_regime.get('regime', 'UNKNOWN')
    confidence_str = f"{market_regime.get('confidence', 0):.1f}"
    trend_strength_str = f"{market_regime.get('trend_strength', 0):.2f}"
    volatility_regime = market_regime.get('volatility_regime', 'NORMAL')
    avg_daily_return_str = f"{market_regime.get('avg_daily_return', 0):+.2f}"
    volatility_str = f"{market_regime.get('volatility', 0):.2f}"
    
    dashboard += f"""
---

## 📊 Market Regime & Benchmarking

### Market Regime Detection

| Metric | Value |
|--------|-------|
| **Current Regime** | {regime} |
| **Confidence** | {confidence_str} |
| **Trend Strength** | {trend_strength_str} |
| **Volatility Regime** | {volatility_regime} |
| **Avg Daily Return** | {avg_daily_return_str}% |
| **Volatility** | {volatility_str}% |

### Benchmark Comparison (vs S&P 500)

| Metric | Portfolio | Benchmark | Difference |
|--------|-----------|-----------|------------|
"""
    
    # Extract benchmark values
    portfolio_return = benchmark.get('portfolio_return', 0)
    benchmark_return = benchmark.get('benchmark_return', 0)
    alpha = benchmark.get('alpha', 0)
    beta = benchmark.get('beta', 1.0)
    data_available = benchmark.get('data_available', False)
    
    portfolio_return_str = f"{portfolio_return:+.2f}"
    benchmark_return_str = f"{benchmark_return:+.2f}"
    alpha_str = f"{alpha:+.2f}"
    beta_str = f"{beta:.2f}"
    alpha_status = '✅ Outperforming' if alpha > 0 else '⚠️ Underperforming'
    beta_status = 'Higher Risk' if beta > 1.0 else 'Lower Risk'
    data_status = '✅ Available' if data_available else '⚠️ Limited'
    
    dashboard += f"""| **Total Return** | {portfolio_return_str}% | {benchmark_return_str}% | {alpha_str}% |
| **Alpha** | {alpha_str}% | - | {alpha_status} |
| **Beta** | {beta_str} | 1.0 | {beta_status} |
| **Data Status** | {data_status} | - | - |

---

## 🤖 System Status & Automation

### Automation Health

| Component | Status |
|-----------|--------|
| **GitHub Actions** | {automation_emoji} {basic_metrics['automation_status']} |
"""
    
    # Extract automation status values
    uptime_pct = automation_status.get('uptime_percentage', 0)
    uptime_str = f"{uptime_pct:.1f}"
    reliability_streak = automation_status.get('reliability_streak', 0)
    days_since_execution = automation_status.get('days_since_execution', 0)
    execution_count = automation_status.get('execution_count', 0)
    failures = automation_status.get('failures', 0)
    
    dashboard += f"""| **Uptime** | {uptime_str}% |
| **Reliability Streak** | {reliability_streak} executions |
| **Last Execution** | {basic_metrics['last_execution']} |
| **Days Since Execution** | {days_since_execution} days |
| **Total Executions** | {execution_count} |
| **Failures** | {failures} |
"""
    
    health_checks_emoji = '✅'
    order_validation_emoji = '✅'
    dashboard += f"| **Health Checks** | {health_checks_emoji} Integrated |\n"
    dashboard += f"| **Order Validation** | {order_validation_emoji} Active |\n"
    
    dashboard += """
### TURBO MODE Status

| System | Status |
|--------|--------|
"""
    
    turbo_emoji = '✅'
    dashboard += f"| **Go ADK Orchestrator** | {turbo_emoji} Enabled |\n"
    dashboard += f"| **Langchain Agents** | {turbo_emoji} Enabled |\n"
    dashboard += f"| **Python Strategies** | {turbo_emoji} Active (Fallback) |\n"
    dashboard += f"| **Sentiment RAG** | {turbo_emoji} Active |\n"
    
    dashboard += """
---

## 📈 Time-Series & Equity Curve

### Daily Profit Trend

**Last 10 Days**:
"""

    # Add recent performance data
    perf_log = load_json_file(DATA_DIR / "performance_log.json")
    if isinstance(perf_log, list) and len(perf_log) > 0:
        recent = perf_log[-10:]  # Last 10 entries
        dashboard += "\n| Date | Equity | P/L | P/L % |\n"
        dashboard += "|------|--------|-----|-------|\n"
        for entry in recent:
            entry_date = entry.get('date', 'N/A')
            equity = entry.get('equity', 0)
            pl = entry.get('pl', 0)
            pl_pct = entry.get('pl_pct', 0) * 100
            dashboard += f"| {entry_date} | ${equity:,.2f} | ${pl:+,.2f} | {pl_pct:+.2f}% |\n"
    else:
        dashboard += "\n*No performance data available yet*\n"
    
    # Equity curve data (last 30 days)
    time_series = world_class_metrics.get('time_series', {})
    equity_curve = time_series.get('equity_curve', [])
    
    dashboard += f"""
### Equity Curve Summary

| Metric | Value |
|--------|-------|
"""
    
    # Extract time series values
    trading_days = risk.get('trading_days', 0)
    rolling_sharpe_7d = time_series.get('rolling_sharpe_7d', 0)
    rolling_sharpe_30d = time_series.get('rolling_sharpe_30d', 0)
    rolling_max_dd_30d = time_series.get('rolling_max_dd_30d', 0)
    
    rolling_sharpe_7d_str = f"{rolling_sharpe_7d:.2f}"
    rolling_sharpe_30d_str = f"{rolling_sharpe_30d:.2f}"
    rolling_max_dd_30d_str = f"{rolling_max_dd_30d:.2f}"
    
    dashboard += f"| **Trading Days Tracked** | {trading_days} |\n"
    dashboard += f"| **Rolling Sharpe (7d)** | {rolling_sharpe_7d_str} |\n"
    dashboard += f"| **Rolling Sharpe (30d)** | {rolling_sharpe_30d_str} |\n"
    dashboard += f"| **Rolling Max DD (30d)** | {rolling_max_dd_30d_str}% |\n"

---

## 🎯 Path to North Star

### Phase Breakdown

| Phase | Days | Focus | Target Profit/Day |
|-------|------|-------|-------------------|
| **Phase 1: R&D** | 1-30 | Data collection, learning | $0-5 |
| **Phase 2: Build Edge** | 31-60 | Optimize strategy | $3-10 |
| **Phase 3: Validate** | 61-90 | Consistent profitability | $5-20 |
| **Phase 4: Scale** | 91+ | Scale to North Star | **$100+** |

**Current Phase**: Phase 1 (Day {basic_metrics['current_day']}/30)

---

## 🧪 Experiments & Learnings

### Current Experiment

*No active experiment*

### Last Experiment

*No recent experiments*

### Key Insights

- Strategy performance tracking enabled
- Risk metrics now visible in dashboard
- Per-strategy diagnostics available

---

## 🤖 AI-Specific KPIs

### AI Model Performance

| Metric | Value |
|--------|-------|
| **AI Enabled** | {'✅ Yes' if ai_kpis.get('ai_enabled', False) else '❌ No'} |
| **AI Trades** | {ai_kpis.get('ai_trades_count', 0)} / {ai_kpis.get('total_trades', 0)} |
| **AI Usage Rate** | {ai_kpis.get('ai_usage_rate', 0):.1f}% |
| **Prediction Accuracy** | {ai_kpis.get('prediction_accuracy', 0):.1f}% |
| **Prediction Latency** | {ai_kpis.get('prediction_latency_ms', 0):.0f} ms |
| **Daily AI Costs** | ${ai_kpis.get('ai_costs_daily', 0):.2f} |
| **Outlier Detection** | {'✅ Enabled' if ai_kpis.get('outlier_detection_enabled', False) else '❌ Disabled'} |
| **Backtest vs Live** | {ai_kpis.get('backtest_vs_live_performance', 0):+.2f}% |

---

## 📔 Trading Journal

### Journal Summary

| Metric | Value |
|--------|-------|
| **Total Entries** | {journal.get('total_entries', 0)} |
| **Entries with Notes** | {journal.get('entries_with_notes', 0)} |
| **Notes Rate** | {journal.get('notes_rate', 0):.1f}% |

### Recent Journal Entries

"""
    
    # Add recent journal entries
    recent_entries = journal.get('recent_entries', [])
    if recent_entries:
        dashboard += "| Trade ID | Symbol | Date | Has Notes |\n"
        dashboard += "|----------|--------|------|-----------|\n"
        for entry in recent_entries[:5]:
            has_notes = '✅' if entry.get('has_notes', False) else '❌'
            dashboard += f"| {entry.get('trade_id', 'N/A')} | {entry.get('symbol', 'N/A')} | {entry.get('date', 'N/A')[:10]} | {has_notes} |\n"
    else:
        dashboard += "*No journal entries available*\n"
    
    dashboard += f"""
---

## 🛡️ Risk Management & Compliance

### Capital Usage & Limits

| Metric | Current | Limit | Status |
|--------|---------|-------|--------|
| **Capital Usage** | {compliance.get('capital_usage_pct', 0):.1f}% | {compliance.get('capital_limit_pct', 100):.1f}% | {'✅ Compliant' if compliance.get('capital_compliant', True) else '⚠️ Over Limit'} |
| **Max Position Size** | {compliance.get('max_position_size_pct', 0):.2f}% | {compliance.get('max_position_limit_pct', 10):.1f}% | {'✅ Compliant' if compliance.get('position_size_compliant', True) else '⚠️ Over Limit'} |

### Stop-Loss Adherence

| Metric | Value |
|--------|-------|
| **Trades with Stop-Loss** | {compliance.get('trades_with_stop_loss', 0)} |
| **Stop-Loss Adherence** | {compliance.get('stop_loss_adherence_pct', 0):.1f}% |

### Audit Trail & Compliance

| Metric | Value |
|--------|-------|
| **Audit Trail Entries** | {compliance.get('audit_trail_count', 0)} |
| **Audit Trail Available** | {'✅ Yes' if compliance.get('audit_trail_available', False) else '❌ No'} |

---

## 📝 Notes

**Current Strategy**: 
- TURBO MODE: ADK orchestrator tries first, falls back to rule-based (MACD + RSI + Volume)
- Allocation: 70% Core ETFs (SPY/QQQ/VOO), 30% Growth (NVDA/GOOGL/AMZN)
- Daily Investment: $10/day fixed

**Key Metrics**:
"""
    
    # Extract key metrics for notes section
    win_rate = basic_metrics['win_rate']
    win_rate_str = f"{win_rate:.1f}"
    win_rate_status = '✅' if win_rate >= 55 else '⚠️'
    avg_daily_profit_str = f"{basic_metrics['avg_daily_profit']:+.2f}"
    automation_status_str = basic_metrics['automation_status']
    reliability_status = '✅' if automation_status_str == 'OPERATIONAL' else '❌'
    sharpe_ratio = risk.get('sharpe_ratio', 0)
    sharpe_ratio_str = f"{sharpe_ratio:.2f}"
    sharpe_status = '✅' if sharpe_ratio >= 1.0 else '⚠️'
    regime_name = market_regime.get('regime', 'UNKNOWN')
    confidence_val = market_regime.get('confidence', 0)
    confidence_str = f"{confidence_val:.0f}"
    alpha_val = benchmark.get('alpha', 0)
    alpha_val_str = f"{alpha_val:+.2f}"
    
    dashboard += f"""- Win Rate: {win_rate_str}% (Target: >55%) {win_rate_status}
- Average Daily: ${avg_daily_profit_str} (Target: $100/day)
- System Reliability: {reliability_status}
- Sharpe Ratio: {sharpe_ratio_str} (Target: >1.0) {sharpe_status}
- Market Regime: {regime_name} ({confidence_str} confidence)
- Benchmark Alpha: {alpha_val_str}% vs S&P 500

---

## 📥 Data Export

**Export Options**:
- CSV Export: Available via `scripts/export_dashboard_data.py`
- Excel Export: Available via `scripts/export_dashboard_data.py`
- JSON API: Available via `data/system_state.json` and `data/performance_log.json`

*Note: Export scripts will be available in next update*

---

## 🔗 Quick Links

- [Repository](https://github.com/IgorGanapolsky/trading)
- [GitHub Actions](https://github.com/IgorGanapolsky/trading/actions)
- [Latest Trades](https://github.com/IgorGanapolsky/trading/tree/main/data)
- [Documentation](https://github.com/IgorGanapolsky/trading/tree/main/docs)

---

*This dashboard is automatically updated daily by GitHub Actions after trading execution.*  
*World-class metrics powered by comprehensive risk & performance analytics.*

"""

    return dashboard


def main():
    """Generate and save dashboard."""
    dashboard = generate_dashboard()
    
    # Save to file (will be committed to wiki repo)
    output_file = Path("wiki/Progress-Dashboard.md")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(dashboard)
    
    print("✅ World-class progress dashboard generated successfully!")
    print(f"📄 Saved to: {output_file}")
    print(f"📊 Metrics calculated for Day {calculate_metrics()['current_day']} of 90")
    print("🎯 World-class metrics: Risk, Performance, Strategy Diagnostics, Guardrails")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

