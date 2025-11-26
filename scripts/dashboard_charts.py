#!/usr/bin/env python3
"""
Chart Generation for World-Class Dashboard

Generates visualizations for the trading dashboard:
- Equity curve
- Drawdown chart
- Daily P/L distribution
- Rolling Sharpe
- Win/loss distribution
- Trade holding time histogram

Uses matplotlib to create images that can be embedded in markdown.
"""
import os
import sys
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DATA_DIR = Path("data")
CHARTS_DIR = Path("wiki") / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_equity_curve_chart(perf_log: List[Dict], output_path: Optional[Path] = None) -> Optional[str]:
    """Generate equity curve chart."""
    if not MATPLOTLIB_AVAILABLE or not perf_log or len(perf_log) < 2:
        return None
    
    # Extract data
    dates = []
    equity_values = []
    for entry in perf_log:
        date_str = entry.get('date', '')
        equity = entry.get('equity', 100000)
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str)
                dates.append(dt)
                equity_values.append(equity)
            except:
                pass
    
    if len(dates) < 2:
        return None
    
    # Create chart
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, equity_values, linewidth=2, color='#2563eb', label='Portfolio Equity')
    ax.fill_between(dates, equity_values, alpha=0.3, color='#2563eb')
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Equity ($)', fontsize=10)
    ax.set_title('Equity Curve', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save
    if output_path is None:
        output_path = CHARTS_DIR / "equity_curve.png"
    
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return f"charts/equity_curve.png"


def generate_drawdown_chart(perf_log: List[Dict], output_path: Optional[Path] = None) -> Optional[str]:
    """Generate drawdown chart."""
    if not MATPLOTLIB_AVAILABLE or not perf_log or len(perf_log) < 2:
        return None
    
    # Extract data
    dates = []
    equity_values = []
    for entry in perf_log:
        date_str = entry.get('date', '')
        equity = entry.get('equity', 100000)
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str)
                dates.append(dt)
                equity_values.append(equity)
            except:
                pass
    
    if len(dates) < 2:
        return None
    
    # Calculate drawdown
    peak = equity_values[0]
    drawdowns = []
    for equity in equity_values:
        if equity > peak:
            peak = equity
        drawdown = ((peak - equity) / peak * 100) if peak > 0 else 0.0
        drawdowns.append(drawdown)
    
    # Create chart
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.fill_between(dates, drawdowns, 0, alpha=0.5, color='#dc2626', label='Drawdown')
    ax.plot(dates, drawdowns, linewidth=2, color='#dc2626')
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Drawdown (%)', fontsize=10)
    ax.set_title('Drawdown Over Time', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save
    if output_path is None:
        output_path = CHARTS_DIR / "drawdown.png"
    
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return f"charts/drawdown.png"


def generate_daily_pl_chart(perf_log: List[Dict], output_path: Optional[Path] = None) -> Optional[str]:
    """Generate daily P/L bar chart."""
    if not MATPLOTLIB_AVAILABLE or not perf_log or len(perf_log) < 2:
        return None
    
    # Extract data
    dates = []
    pl_values = []
    for entry in perf_log:
        date_str = entry.get('date', '')
        pl = entry.get('pl', 0)
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str)
                dates.append(dt)
                pl_values.append(pl)
            except:
                pass
    
    if len(dates) < 2:
        return None
    
    # Create chart
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ['#10b981' if pl >= 0 else '#ef4444' for pl in pl_values]
    ax.bar(dates, pl_values, color=colors, alpha=0.7, width=0.8)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Daily P/L ($)', fontsize=10)
    ax.set_title('Daily Profit/Loss', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save
    if output_path is None:
        output_path = CHARTS_DIR / "daily_pl.png"
    
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return f"charts/daily_pl.png"


def generate_rolling_sharpe_chart(perf_log: List[Dict], window: int = 7, output_path: Optional[Path] = None) -> Optional[str]:
    """Generate rolling Sharpe ratio chart."""
    if not MATPLOTLIB_AVAILABLE or not perf_log or len(perf_log) < window + 1:
        return None
    
    # Extract returns
    dates = []
    equity_values = []
    for entry in perf_log:
        date_str = entry.get('date', '')
        equity = entry.get('equity', 100000)
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str)
                dates.append(dt)
                equity_values.append(equity)
            except:
                pass
    
    if len(dates) < window + 1:
        return None
    
    # Calculate rolling Sharpe
    returns = []
    for i in range(1, len(equity_values)):
        if equity_values[i-1] > 0:
            ret = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
            returns.append(ret)
    
    if len(returns) < window:
        return None
    
    rolling_sharpe = []
    rolling_dates = dates[window:]
    
    for i in range(window, len(returns)):
        window_returns = returns[i-window:i]
        if len(window_returns) > 1:
            mean_ret = np.mean(window_returns)
            std_ret = np.std(window_returns)
            sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0
            rolling_sharpe.append(sharpe)
        else:
            rolling_sharpe.append(0.0)
    
    # Create chart
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(rolling_dates, rolling_sharpe, linewidth=2, color='#8b5cf6', label=f'Rolling Sharpe ({window}d)')
    ax.axhline(y=1.0, color='green', linestyle='--', linewidth=1, label='Target (1.0)')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Sharpe Ratio', fontsize=10)
    ax.set_title(f'Rolling Sharpe Ratio ({window}-Day Window)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save
    if output_path is None:
        output_path = CHARTS_DIR / f"rolling_sharpe_{window}d.png"
    
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return f"charts/rolling_sharpe_{window}d.png"


def generate_all_charts(perf_log: List[Dict]) -> Dict[str, Optional[str]]:
    """Generate all charts and return paths."""
    charts = {}
    
    charts['equity_curve'] = generate_equity_curve_chart(perf_log)
    charts['drawdown'] = generate_drawdown_chart(perf_log)
    charts['daily_pl'] = generate_daily_pl_chart(perf_log)
    charts['rolling_sharpe_7d'] = generate_rolling_sharpe_chart(perf_log, window=7)
    charts['rolling_sharpe_30d'] = generate_rolling_sharpe_chart(perf_log, window=30)
    
    return charts


if __name__ == "__main__":
    # Test chart generation
    from scripts.dashboard_metrics import load_json_file
    
    perf_log = load_json_file(DATA_DIR / "performance_log.json")
    if isinstance(perf_log, list):
        charts = generate_all_charts(perf_log)
        print("Generated charts:")
        for name, path in charts.items():
            if path:
                print(f"  ✅ {name}: {path}")
            else:
                print(f"  ❌ {name}: Not generated (insufficient data)")

