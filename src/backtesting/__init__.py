"""
Backtesting Module

Lightweight backtesting engine for validating trading strategies on historical data.

Modules:
    - backtest_engine: Main backtesting engine
    - backtest_results: Results data structure and reporting

Author: Trading System
Created: 2025-11-02
"""

from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.backtest_results import BacktestResults

__all__ = ["BacktestEngine", "BacktestResults"]
