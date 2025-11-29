"""
Backtest Engine Module

This module provides a lightweight backtesting engine for validating trading strategies
on historical data before deploying them in live trading. It simulates strategy execution
day-by-day and calculates comprehensive performance metrics.

Features:
    - Simulates daily strategy execution on historical data
    - Tracks portfolio value, trades, and P/L over time
    - Calculates key performance metrics (Sharpe, win rate, drawdown)
    - Works with existing CoreStrategy class
    - Uses yfinance for historical price data

Author: Trading System
Created: 2025-11-02
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from src.backtesting.backtest_results import BacktestResults


# Configure logging
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Lightweight backtesting engine for momentum-based ETF trading strategies.

    This engine simulates the execution of a trading strategy on historical data,
    tracking portfolio performance and calculating comprehensive metrics.

    Attributes:
        strategy: Trading strategy instance to backtest
        start_date: Start date for backtest (YYYY-MM-DD format)
        end_date: End date for backtest (YYYY-MM-DD format)
        initial_capital: Starting capital amount
        current_capital: Current available capital
        portfolio_value: Current total portfolio value
        positions: Current holdings {symbol: quantity}
        trades: List of executed trades
        equity_curve: Daily portfolio values
        dates: Trading dates
    """

    def __init__(
        self,
        strategy: Any,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0,
    ):
        """
        Initialize the backtest engine.

        Args:
            strategy: Trading strategy instance (e.g., CoreStrategy)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            initial_capital: Starting capital amount (default: $100,000)

        Raises:
            ValueError: If dates are invalid or strategy is None
        """
        if strategy is None:
            raise ValueError("Strategy cannot be None")

        try:
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")

        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")

        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive")

        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.portfolio_value = initial_capital

        # Portfolio state
        self.positions: Dict[str, float] = {}
        self.position_costs: Dict[str, float] = {}  # Track cost basis

        # Performance tracking
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = [initial_capital]
        self.dates: List[str] = [start_date]

        # Price cache for efficiency
        self.price_cache: Dict[str, pd.DataFrame] = {}

        logger.info(f"Backtest engine initialized: {start_date} to {end_date}")
        logger.info(f"Initial capital: ${initial_capital:,.2f}")
        logger.info(f"Strategy: {type(strategy).__name__}")

    def run(self) -> BacktestResults:
        """
        Execute the backtest and return comprehensive results.

        This method:
        1. Iterates through each trading day in the date range
        2. Simulates strategy execution for each day
        3. Tracks portfolio performance
        4. Calculates final metrics
        5. Returns BacktestResults object

        Returns:
            BacktestResults object containing all performance data and metrics

        Raises:
            Exception: If backtest execution fails
        """
        logger.info("=" * 80)
        logger.info("STARTING BACKTEST EXECUTION")
        logger.info("=" * 80)

        try:
            # Pre-load price data for all ETFs in strategy universe
            self._preload_price_data()

            # Get trading dates (weekdays only)
            trading_dates = self._get_trading_dates()

            logger.info(f"Total trading days: {len(trading_dates)}")

            # Simulate trading for each day
            for i, date in enumerate(trading_dates):
                self._simulate_trading_day(date)

                # Log progress every 10 days
                if (i + 1) % 10 == 0 or i == len(trading_dates) - 1:
                    logger.info(
                        f"Progress: {i+1}/{len(trading_dates)} days "
                        f"({(i+1)/len(trading_dates)*100:.1f}%) - "
                        f"Portfolio: ${self.portfolio_value:,.2f}"
                    )

            # Calculate final metrics
            results = self._calculate_results()

            logger.info("=" * 80)
            logger.info("BACKTEST COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Total Trades: {results.total_trades}")
            logger.info(
                f"Final Capital: ${results.final_capital:,.2f} "
                f"({results.total_return:+.2f}%)"
            )
            logger.info(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
            logger.info(f"Max Drawdown: {results.max_drawdown:.2f}%")
            logger.info(f"Win Rate: {results.win_rate:.1f}%")

            return results

        except Exception as e:
            logger.error(f"Backtest execution failed: {e}", exc_info=True)
            raise

    def _preload_price_data(self) -> None:
        """
        Pre-load historical price data for all ETFs using Alpaca API.
        More reliable than yfinance free tier.
        """
        logger.info("Pre-loading historical price data from Alpaca...")

        # Initialize Alpaca client
        alpaca_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret = os.getenv("ALPACA_SECRET_KEY")

        if not alpaca_key or not alpaca_secret:
            logger.error("Alpaca API credentials not found. Set ALPACA_API_KEY and ALPACA_SECRET_KEY")
            return

        client = StockHistoricalDataClient(alpaca_key, alpaca_secret)

        etf_universe = getattr(self.strategy, "etf_universe", ["SPY", "QQQ", "VOO"])

        for symbol in etf_universe:
            try:
                # Get historical bars from Alpaca
                # Add 200 day buffer for momentum calculations
                start_with_buffer = datetime.strptime(self.start_date.strftime("%Y-%m-%d"), "%Y-%m-%d") - timedelta(days=200)
                end_with_buffer = datetime.strptime(self.end_date.strftime("%Y-%m-%d"), "%Y-%m-%d") + timedelta(days=1)

                req = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Day,
                    start=start_with_buffer,
                    end=end_with_buffer,
                    adjustment='all'
                )

                bars = client.get_stock_bars(req).df

                if bars is not None and not bars.empty:
                    # Reset index to get timestamp as column if needed, or just use it
                    # Alpaca-py returns MultiIndex (symbol, timestamp) or just timestamp if single symbol?
                    # Usually MultiIndex. Let's check.

                    if 'symbol' in bars.index.names:
                        bars = bars.droplevel('symbol')

                    # Rename columns to match yfinance format
                    bars = bars.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })

                    self.price_cache[symbol] = bars
                    logger.info(f"Loaded {len(bars)} bars for {symbol} from Alpaca")
                else:
                    logger.warning(f"No data returned for {symbol}")

            except Exception as e:
                logger.warning(f"Failed to load data for {symbol}: {e}")

    def _get_trading_dates(self) -> List[datetime]:
        """
        Generate list of trading dates (weekdays only) in the backtest period.

        Returns:
            List of datetime objects representing trading days
        """
        dates = []
        current_date = self.start_date

        while current_date <= self.end_date:
            # Only include weekdays (Monday=0 to Friday=4)
            if current_date.weekday() < 5:
                dates.append(current_date)
            current_date += timedelta(days=1)

        return dates

    def _simulate_trading_day(self, date: datetime) -> None:
        """
        Simulate strategy execution for a single trading day.

        Args:
            date: Trading date to simulate
        """
        date_str = date.strftime("%Y-%m-%d")

        # Update portfolio value with current prices
        self._update_portfolio_value(date)

        # Get the best ETF to buy from strategy
        try:
            # Calculate momentum scores for this date
            # Skip sentiment in backtest mode (would require live API calls)
            momentum_scores = []

            for symbol in self.strategy.etf_universe:
                try:
                    # Get historical data up to this date
                    hist = self._get_historical_data(symbol, date)
                    if hist is None:
                        logger.warning(f"{date_str}: No historical data for {symbol}")
                        continue
                    if len(hist) < 50:
                        logger.warning(f"{date_str}: Insufficient data for {symbol}: {len(hist)} bars (need 50)")
                        continue

                    # Calculate momentum score using strategy's method
                    # We need to temporarily modify yfinance calls to use cached data
                    score = self._calculate_momentum_for_date(symbol, date)
                    if score is not None:
                        momentum_scores.append({"symbol": symbol, "score": score})
                        logger.info(f"{date_str}: {symbol} momentum={score:.2f}")
                    else:
                        logger.warning(f"{date_str}: Momentum calculation returned None for {symbol}")

                except Exception as e:
                    logger.warning(f"Failed to calculate momentum for {symbol}: {e}")
                    continue

            if not momentum_scores:
                logger.warning(f"{date_str}: No valid momentum scores")
                return

            # Select best ETF
            momentum_scores.sort(key=lambda x: x["score"], reverse=True)
            best_etf = momentum_scores[0]["symbol"]

            # Get current price
            price = self._get_price(best_etf, date)
            if price is None:
                logger.debug(f"{date_str}: No price available for {best_etf}")
                return

            # Execute trade if we have capital
            daily_allocation = self.strategy.daily_allocation
            if self.current_capital >= daily_allocation:
                quantity = daily_allocation / price

                # Record trade
                trade = {
                    "date": date_str,
                    "symbol": best_etf,
                    "action": "buy",
                    "quantity": quantity,
                    "price": price,
                    "amount": daily_allocation,
                    "reason": "Daily DCA purchase",
                }
                self.trades.append(trade)

                # Update positions
                self.positions[best_etf] = self.positions.get(best_etf, 0.0) + quantity
                self.position_costs[best_etf] = (
                    self.position_costs.get(best_etf, 0.0) + daily_allocation
                )
                self.current_capital -= daily_allocation

                logger.debug(
                    f"{date_str}: BUY {quantity:.4f} {best_etf} @ ${price:.2f}"
                )

        except Exception as e:
            logger.debug(f"Error simulating {date_str}: {e}")

        # Record equity curve
        self._update_portfolio_value(date)
        self.equity_curve.append(self.portfolio_value)
        self.dates.append(date_str)

    def _get_historical_data(self, symbol: str, date: datetime) -> Optional[pd.DataFrame]:
        """
        Get historical data for a symbol up to a specific date.

        Args:
            symbol: ETF symbol
            date: Date to get data up to

        Returns:
            DataFrame with historical data or None if unavailable
        """
        if symbol not in self.price_cache:
            return None

        hist = self.price_cache[symbol]

        # Convert date to timezone-aware datetime for comparison with Alpaca data
        if date.tzinfo is None:
            import pytz
            date = pytz.UTC.localize(date)

        # Filter to only include data up to the simulation date
        hist_filtered = hist[hist.index <= date]

        return hist_filtered if len(hist_filtered) > 0 else None

    def _calculate_momentum_for_date(self, symbol: str, date: datetime) -> Optional[float]:
        """
        Calculate momentum score for a symbol at a specific date.

        Args:
            symbol: ETF symbol
            date: Date to calculate momentum for

        Returns:
            Momentum score or None if calculation fails
        """
        try:
            hist = self._get_historical_data(symbol, date)
            if hist is None or len(hist) < 126:  # Need at least 6 months
                return None

            # Simple momentum calculation (weighted returns)
            # This is a simplified version - adjust as needed
            returns_1m = self._calculate_period_return(hist, 21)
            returns_3m = self._calculate_period_return(hist, 63)
            returns_6m = self._calculate_period_return(hist, 126)

            momentum = (
                returns_1m * 0.5 + returns_3m * 0.3 + returns_6m * 0.2
            ) * 100

            return momentum

        except Exception as e:
            logger.debug(f"Momentum calculation failed for {symbol}: {e}")
            return None

    def _calculate_period_return(self, hist: pd.DataFrame, periods: int) -> float:
        """
        Calculate return over specified number of periods.

        Args:
            hist: Historical price DataFrame
            periods: Number of periods to look back

        Returns:
            Period return as decimal
        """
        if len(hist) < periods:
            periods = len(hist) - 1

        if periods <= 0:
            return 0.0

        end_price = hist["Close"].iloc[-1]
        start_price = hist["Close"].iloc[-periods]

        return (end_price - start_price) / start_price

    def _get_price(self, symbol: str, date: datetime) -> Optional[float]:
        """
        Get the closing price for a symbol on a specific date.

        Args:
            symbol: ETF symbol
            date: Date to get price for

        Returns:
            Closing price or None if unavailable
        """
        hist = self._get_historical_data(symbol, date)
        if hist is None or len(hist) == 0:
            return None

        return float(hist["Close"].iloc[-1])

    def _update_portfolio_value(self, date: datetime) -> None:
        """
        Update total portfolio value based on current positions and prices.

        Args:
            date: Current date for price lookup
        """
        positions_value = 0.0

        for symbol, quantity in self.positions.items():
            price = self._get_price(symbol, date)
            if price:
                positions_value += quantity * price

        self.portfolio_value = self.current_capital + positions_value

    def _calculate_results(self) -> BacktestResults:
        """
        Calculate comprehensive backtest results and metrics.

        Returns:
            BacktestResults object with all performance data
        """
        # Basic metrics
        final_capital = self.portfolio_value
        total_return = (
            (final_capital - self.initial_capital) / self.initial_capital * 100
        )

        # Calculate daily returns for Sharpe ratio
        daily_returns = np.diff(self.equity_curve) / self.equity_curve[:-1]

        # Sharpe ratio
        if len(daily_returns) > 1:
            mean_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            risk_free_rate_daily = 0.04 / 252
            sharpe_ratio = (
                (mean_return - risk_free_rate_daily) / std_return * np.sqrt(252)
                if std_return > 0
                else 0.0
            )
        else:
            sharpe_ratio = 0.0

        # Max drawdown
        cumulative_returns = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(np.min(drawdown)) * 100

        # Win rate
        positive_days = np.sum(daily_returns > 0)
        win_rate = (positive_days / len(daily_returns) * 100) if len(daily_returns) > 0 else 0.0

        # Trade statistics
        total_trades = len(self.trades)
        profitable_trades = 0

        # Simple profit calculation per trade (simplified)
        for trade in self.trades:
            symbol = trade["symbol"]
            buy_price = trade["price"]
            # Get final price for this symbol
            final_price = self._get_price(symbol, self.end_date)
            if final_price and final_price > buy_price:
                profitable_trades += 1

        average_trade_return = (total_return / total_trades) if total_trades > 0 else 0.0

        results = BacktestResults(
            trades=self.trades,
            equity_curve=self.equity_curve,
            dates=self.dates,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            average_trade_return=average_trade_return,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            start_date=self.start_date.strftime("%Y-%m-%d"),
            end_date=self.end_date.strftime("%Y-%m-%d"),
            trading_days=len(self.dates) - 1,
        )

        return results


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # This example shows how to use the backtest engine
    # In practice, you would import and use your actual CoreStrategy

    print("Backtest Engine - Example Usage")
    print("=" * 80)
    print("\nTo use this engine with your CoreStrategy:")
    print("\n  from src.strategies.core_strategy import CoreStrategy")
    print("  from src.backtesting.backtest_engine import BacktestEngine")
    print("\n  strategy = CoreStrategy(daily_allocation=6.0, use_sentiment=False)")
    print("  engine = BacktestEngine(")
    print("      strategy=strategy,")
    print('      start_date="2025-09-01",')
    print('      end_date="2025-10-31",')
    print("      initial_capital=100000")
    print("  )")
    print("  results = engine.run()")
    print("  print(results.generate_report())")
    print("\n" + "=" * 80)
