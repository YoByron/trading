#!/usr/bin/env python3
"""
World-Class Trading Dashboard Metrics Calculator

Calculates comprehensive metrics for AI trading dashboard including:
- Risk & Performance Depth (drawdown, Sharpe, Sortino, volatility, VaR)
- Strategy & Model Diagnostics (per-strategy performance, signal quality)
- Time-Series & Cohort Analytics (equity curve, rolling metrics)
- Operational Guardrails & Safety (risk limits, auditability)

This module provides the foundation for a professional quant dashboard.
"""
import os
import sys
import json
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DATA_DIR = Path("data")


def load_json_file(filepath: Path) -> Any:
    """Load JSON file, return empty dict/list if not found."""
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception:
            return {} if 'json' in str(filepath) else []
    return {} if 'json' in str(filepath) else []


class TradingMetricsCalculator:
    """
    Comprehensive metrics calculator for world-class trading dashboard.
    """
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.risk_free_rate = 0.04  # 4% annual risk-free rate
        
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all world-class metrics for the dashboard.
        
        Returns:
            Dictionary containing all calculated metrics organized by category
        """
        # Load data sources
        system_state = load_json_file(self.data_dir / "system_state.json")
        perf_log = load_json_file(self.data_dir / "performance_log.json")
        
        # Ensure perf_log is a list
        if not isinstance(perf_log, list):
            perf_log = []
        
        # Get account info
        account = system_state.get('account', {})
        starting_balance = account.get('starting_balance', 100000.0)
        current_equity = account.get('current_equity', starting_balance)
        
        # Get performance data
        performance = system_state.get('performance', {})
        closed_trades = performance.get('closed_trades', [])
        open_positions = performance.get('open_positions', [])
        
        # Load all trade files
        all_trades = self._load_all_trades()
        
        # Calculate metrics
        metrics = {
            'account_summary': self._calculate_account_summary(
                account, starting_balance, current_equity
            ),
            'risk_metrics': self._calculate_risk_metrics(
                perf_log, starting_balance, current_equity
            ),
            'performance_metrics': self._calculate_performance_metrics(
                perf_log, closed_trades, all_trades
            ),
            'strategy_metrics': self._calculate_strategy_metrics(
                system_state, closed_trades, all_trades
            ),
            'exposure_metrics': self._calculate_exposure_metrics(
                open_positions, current_equity, all_trades
            ),
            'risk_guardrails': self._calculate_risk_guardrails(
                system_state, perf_log, current_equity
            ),
            'time_series': self._calculate_time_series_metrics(perf_log),
            'signal_quality': self._calculate_signal_quality(all_trades, closed_trades),
        }
        
        return metrics
    
    def _load_all_trades(self) -> List[Dict]:
        """Load all trade files and combine into single list."""
        all_trades = []
        
        # Find all trade files
        trade_files = list(self.data_dir.glob("trades_*.json"))
        
        for trade_file in trade_files:
            trades = load_json_file(trade_file)
            if isinstance(trades, list):
                for trade in trades:
                    trade['trade_date'] = trade_file.stem.replace('trades_', '')
                    all_trades.append(trade)
        
        return all_trades
    
    def _calculate_account_summary(
        self, account: Dict, starting_balance: float, current_equity: float
    ) -> Dict[str, Any]:
        """Calculate basic account summary metrics."""
        total_pl = current_equity - starting_balance
        total_pl_pct = (total_pl / starting_balance * 100) if starting_balance > 0 else 0.0
        
        return {
            'starting_balance': starting_balance,
            'current_equity': current_equity,
            'total_pl': total_pl,
            'total_pl_pct': total_pl_pct,
            'cash': account.get('cash', current_equity),
            'positions_value': account.get('positions_value', 0.0),
        }
    
    def _calculate_risk_metrics(
        self, perf_log: List[Dict], starting_balance: float, current_equity: float
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics."""
        if not perf_log or len(perf_log) < 2:
            return {
                'max_drawdown_pct': 0.0,
                'current_drawdown_pct': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'volatility_annualized': 0.0,
                'worst_daily_loss': 0.0,
                'var_95': 0.0,
                'peak_equity': current_equity,
            }
        
        # Extract equity curve
        equity_values = [entry.get('equity', starting_balance) for entry in perf_log]
        dates = [entry.get('date', '') for entry in perf_log]
        
        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(equity_values)):
            if equity_values[i-1] > 0:
                daily_return = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
                daily_returns.append(daily_return)
        
        if not daily_returns:
            return {
                'max_drawdown_pct': 0.0,
                'current_drawdown_pct': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'volatility_annualized': 0.0,
                'worst_daily_loss': 0.0,
                'var_95': 0.0,
                'peak_equity': current_equity,
            }
        
        # Calculate max drawdown
        peak = equity_values[0]
        max_drawdown_pct = 0.0
        peak_equity = peak
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
                peak_equity = peak
            drawdown_pct = ((peak - equity) / peak * 100) if peak > 0 else 0.0
            if drawdown_pct > max_drawdown_pct:
                max_drawdown_pct = drawdown_pct
        
        # Current drawdown
        current_drawdown_pct = (
            ((peak_equity - current_equity) / peak_equity * 100)
            if peak_equity > 0 else 0.0
        )
        
        # Calculate Sharpe ratio
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        risk_free_rate_daily = self.risk_free_rate / 252
        
        sharpe_ratio = 0.0
        if std_return > 0:
            excess_return = mean_return - risk_free_rate_daily
            sharpe_ratio = (excess_return / std_return) * np.sqrt(252)
        
        # Calculate Sortino ratio (downside deviation only)
        downside_returns = [r for r in daily_returns if r < 0]
        sortino_ratio = 0.0
        if downside_returns:
            downside_std = np.std(downside_returns)
            if downside_std > 0:
                sortino_ratio = (mean_return - risk_free_rate_daily) / downside_std * np.sqrt(252)
        
        # Annualized volatility
        volatility_annualized = std_return * np.sqrt(252) * 100 if std_return > 0 else 0.0
        
        # Worst daily loss
        worst_daily_loss = min(daily_returns) * 100 if daily_returns else 0.0
        
        # VaR (95th percentile)
        var_95 = np.percentile(daily_returns, 5) * 100 if daily_returns else 0.0
        
        return {
            'max_drawdown_pct': max_drawdown_pct,
            'current_drawdown_pct': current_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'volatility_annualized': volatility_annualized,
            'worst_daily_loss': worst_daily_loss,
            'var_95': var_95,
            'peak_equity': peak_equity,
            'trading_days': len(daily_returns),
        }
    
    def _calculate_performance_metrics(
        self, perf_log: List[Dict], closed_trades: List[Dict], all_trades: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate performance metrics including profit factor and expectancy."""
        if not closed_trades:
            return {
                'profit_factor': 0.0,
                'expectancy_per_trade': 0.0,
                'expectancy_per_r': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'win_rate': 0.0,
            }
        
        # Calculate profit factor
        gross_profit = sum(t.get('pl', 0) for t in closed_trades if t.get('pl', 0) > 0)
        gross_loss = abs(sum(t.get('pl', 0) for t in closed_trades if t.get('pl', 0) < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0
        
        # Calculate expectancy
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.get('pl', 0) > 0]
        losing_trades = [t for t in closed_trades if t.get('pl', 0) < 0]
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
        avg_win = np.mean([t.get('pl', 0) for t in winning_trades]) if winning_trades else 0.0
        avg_loss = np.mean([abs(t.get('pl', 0)) for t in losing_trades]) if losing_trades else 0.0
        
        # Expectancy per trade ($)
        expectancy_per_trade = (
            (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)
            if total_trades > 0 else 0.0
        )
        
        # Expectancy per R (assuming 1% risk per trade)
        # R = risk per trade = 1% of account
        # For simplicity, we'll use avg_win/avg_loss ratio
        expectancy_per_r = (
            (avg_win / avg_loss) if avg_loss > 0 else 0.0
        )
        
        # Largest win/loss
        largest_win = max([t.get('pl', 0) for t in closed_trades], default=0.0)
        largest_loss = min([t.get('pl', 0) for t in closed_trades], default=0.0)
        
        return {
            'profit_factor': profit_factor,
            'expectancy_per_trade': expectancy_per_trade,
            'expectancy_per_r': expectancy_per_r,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
        }
    
    def _calculate_strategy_metrics(
        self, system_state: Dict, closed_trades: List[Dict], all_trades: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate per-strategy performance metrics."""
        strategies = system_state.get('strategies', {})
        strategy_performance = {}
        
        for strategy_id, strategy_data in strategies.items():
            strategy_name = strategy_data.get('name', strategy_id)
            
            # Filter trades for this strategy
            strategy_trades = [
                t for t in closed_trades
                if t.get('tier', '').lower() == strategy_id.lower()
            ]
            
            if not strategy_trades:
                continue
            
            # Calculate metrics for this strategy
            total_pl = sum(t.get('pl', 0) for t in strategy_trades)
            winning = [t for t in strategy_trades if t.get('pl', 0) > 0]
            win_rate = (len(winning) / len(strategy_trades) * 100) if strategy_trades else 0.0
            
            # Simple Sharpe (would need daily returns per strategy for accurate)
            sharpe = 0.0  # Placeholder - would need strategy-specific equity curve
            
            # Max drawdown (simplified)
            max_dd = 0.0  # Placeholder
            
            strategy_performance[strategy_id] = {
                'name': strategy_name,
                'trades': len(strategy_trades),
                'pl': total_pl,
                'win_rate': win_rate,
                'sharpe': sharpe,
                'max_drawdown_pct': max_dd,
            }
        
        return strategy_performance
    
    def _calculate_exposure_metrics(
        self, open_positions: List[Dict], current_equity: float, all_trades: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate exposure by ticker, sector, and asset class."""
        if not open_positions:
            return {
                'by_ticker': {},
                'by_sector': {},
                'by_asset_class': {},
                'largest_position_pct': 0.0,
                'total_exposure': 0.0,
            }
        
        exposure_by_ticker = defaultdict(float)
        exposure_by_sector = defaultdict(float)
        exposure_by_asset_class = defaultdict(float)
        
        # Sector mapping (simplified)
        sector_map = {
            'SPY': 'Index ETF',
            'QQQ': 'Index ETF',
            'VOO': 'Index ETF',
            'NVDA': 'Technology',
            'GOOGL': 'Technology',
            'AMZN': 'Technology',
        }
        
        # Asset class mapping
        asset_class_map = {
            'SPY': 'Index ETF',
            'QQQ': 'Index ETF',
            'VOO': 'Index ETF',
            'NVDA': 'Single Stock',
            'GOOGL': 'Single Stock',
            'AMZN': 'Single Stock',
        }
        
        total_exposure = 0.0
        
        for position in open_positions:
            symbol = position.get('symbol', '')
            amount = position.get('amount', 0.0)
            
            exposure_by_ticker[symbol] += amount
            exposure_by_sector[sector_map.get(symbol, 'Unknown')] += amount
            exposure_by_asset_class[asset_class_map.get(symbol, 'Unknown')] += amount
            total_exposure += amount
        
        # Calculate percentages
        exposure_by_ticker_pct = {
            ticker: (amount / current_equity * 100) if current_equity > 0 else 0.0
            for ticker, amount in exposure_by_ticker.items()
        }
        
        # Largest position
        largest_position_pct = (
            max(exposure_by_ticker_pct.values()) if exposure_by_ticker_pct else 0.0
        )
        
        return {
            'by_ticker': exposure_by_ticker_pct,
            'by_sector': dict(exposure_by_sector),
            'by_asset_class': dict(exposure_by_asset_class),
            'largest_position_pct': largest_position_pct,
            'total_exposure': total_exposure,
        }
    
    def _calculate_risk_guardrails(
        self, system_state: Dict, perf_log: List[Dict], current_equity: float
    ) -> Dict[str, Any]:
        """Calculate risk guardrail status."""
        # Get today's P/L
        today = date.today().isoformat()
        today_entries = [e for e in perf_log if e.get('date') == today]
        daily_pl = today_entries[-1].get('pl', 0.0) if today_entries else 0.0
        
        # Daily loss limit (assume 2% default)
        daily_loss_limit_pct = 2.0
        daily_loss_limit = current_equity * (daily_loss_limit_pct / 100)
        daily_loss_used_pct = (
            (abs(daily_pl) / daily_loss_limit * 100)
            if daily_pl < 0 and daily_loss_limit > 0 else 0.0
        )
        
        # Max position size (assume 10% default)
        max_position_size_pct = 10.0
        
        # Consecutive losses
        performance = system_state.get('performance', {})
        consecutive_losses = performance.get('consecutive_losses', 0)
        
        return {
            'daily_loss_limit': daily_loss_limit,
            'daily_loss_used': abs(daily_pl) if daily_pl < 0 else 0.0,
            'daily_loss_used_pct': daily_loss_used_pct,
            'max_position_size_pct': max_position_size_pct,
            'consecutive_losses': consecutive_losses,
            'consecutive_losses_limit': 5,  # Default limit
        }
    
    def _calculate_time_series_metrics(self, perf_log: List[Dict]) -> Dict[str, Any]:
        """Calculate time-series analytics."""
        if not perf_log or len(perf_log) < 2:
            return {
                'equity_curve': [],
                'rolling_sharpe_7d': 0.0,
                'rolling_sharpe_30d': 0.0,
                'rolling_max_dd_30d': 0.0,
            }
        
        # Equity curve
        equity_curve = [
            {'date': entry.get('date', ''), 'equity': entry.get('equity', 0)}
            for entry in perf_log
        ]
        
        # Rolling metrics (simplified - would need proper windowing)
        rolling_sharpe_7d = 0.0  # Placeholder
        rolling_sharpe_30d = 0.0  # Placeholder
        rolling_max_dd_30d = 0.0  # Placeholder
        
        return {
            'equity_curve': equity_curve[-30:],  # Last 30 days
            'rolling_sharpe_7d': rolling_sharpe_7d,
            'rolling_sharpe_30d': rolling_sharpe_30d,
            'rolling_max_dd_30d': rolling_max_dd_30d,
        }
    
    def _calculate_signal_quality(
        self, all_trades: List[Dict], closed_trades: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate signal quality metrics."""
        # This is a placeholder - would need signal type data in trades
        return {
            'by_signal_type': {},
            'avg_return_1d': 0.0,
            'avg_return_5d': 0.0,
            'avg_return_20d': 0.0,
        }


if __name__ == "__main__":
    calculator = TradingMetricsCalculator()
    metrics = calculator.calculate_all_metrics()
    
    print("=" * 70)
    print("WORLD-CLASS TRADING METRICS")
    print("=" * 70)
    print(json.dumps(metrics, indent=2, default=str))

