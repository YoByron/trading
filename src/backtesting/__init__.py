"""
Backtesting Module

Lightweight backtesting engine for validating trading strategies on historical data.

Modules:
    - backtest_engine: Main backtesting engine
    - backtest_results: Results data structure and reporting
    - walk_forward_matrix: Walk-forward validation with rolling OOS evaluation
    - target_integration: $100/day target evaluation for backtests

Author: Trading System
Created: 2025-11-02
"""

from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.backtest_results import BacktestResults
from src.backtesting.performance_report import PerformanceReporter, PerformanceReport
from src.backtesting.walk_forward import (
    WalkForwardValidator,
    WalkForwardResults,
    WalkForwardFold,
    create_time_aware_split,
)
from src.backtesting.walk_forward_matrix import (
    BacktestMatrixResults,
    LiveVsBacktestTracker,
    WalkForwardMatrixValidator,
    run_walk_forward_matrix,
)
from src.backtesting.target_integration import (
    evaluate_backtest_with_target,
    add_target_section_to_report,
    save_target_evaluation,
    BacktestTargetValidator,
    TargetBacktestReport,
)

__all__ = [
    "BacktestEngine",
    "BacktestResults",
    "BacktestMatrixResults",
    "WalkForwardMatrixValidator",
    "LiveVsBacktestTracker",
    "run_walk_forward_matrix",
    "evaluate_backtest_with_target",
    "add_target_section_to_report",
    "save_target_evaluation",
    "BacktestTargetValidator",
    "TargetBacktestReport",
]
