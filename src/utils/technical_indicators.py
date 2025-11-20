"""
Shared Technical Indicators Utility

This module provides a single source of truth for technical indicator calculations
(MACD, RSI, Volume Ratio) used across the trading system.

Consolidates duplicate logic from:
- scripts/autonomous_trader.py
- src/strategies/core_strategy.py
- src/strategies/growth_strategy.py
"""
import logging
from typing import Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[float, float, float]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    MACD is a trend-following momentum indicator that shows the relationship between
    two exponential moving averages (EMAs) of a security's price.

    Formula:
    - MACD Line = 12-day EMA - 26-day EMA
    - Signal Line = 9-day EMA of MACD Line
    - Histogram = MACD Line - Signal Line

    Trading Signals:
    - Bullish: MACD crosses above signal line (histogram > 0)
    - Bearish: MACD crosses below signal line (histogram < 0)
    - Momentum strength: Larger histogram = stronger momentum

    Args:
        prices: Price series (typically Close prices)
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)

    Returns:
        Tuple of (macd_value, signal_line, histogram)
    """
    if len(prices) < slow_period + signal_period:
        logger.warning(
            f"Insufficient data for MACD calculation: {len(prices)} bars, "
            f"need at least {slow_period + signal_period}"
        )
        return (0.0, 0.0, 0.0)

    # Calculate exponential moving averages
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

    # MACD line = Fast EMA - Slow EMA
    macd_line = ema_fast - ema_slow

    # Signal line = 9-day EMA of MACD line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # MACD histogram = MACD line - Signal line
    histogram = macd_line - signal_line

    # Return most recent values
    return (
        float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
        float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
        float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0,
    )


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index).

    RSI is a momentum oscillator that measures the speed and magnitude of price changes.
    Values range from 0 to 100.

    Trading Signals:
    - Overbought: RSI > 70 (potential sell signal)
    - Oversold: RSI < 30 (potential buy signal)
    - Neutral: 30 < RSI < 70

    Args:
        prices: Price series (typically Close prices)
        period: RSI period (default: 14)

    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        logger.warning(
            f"Insufficient data for RSI calculation: {len(prices)} bars, "
            f"need at least {period + 1}"
        )
        return 50.0  # Neutral RSI

    # Calculate price changes
    delta = prices.diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss.replace(0, np.nan)

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    # Return most recent value
    rsi_value = rsi.iloc[-1]
    if pd.isna(rsi_value):
        return 50.0  # Neutral RSI

    return float(rsi_value)


def calculate_volume_ratio(
    hist: pd.DataFrame, window: int = 20
) -> float:
    """
    Calculate volume ratio (current vs N-day average).

    Volume ratio helps confirm price movements:
    - High volume (>1.5x average) = Strong conviction
    - Low volume (<0.8x average) = Weak conviction

    Args:
        hist: Historical price DataFrame with 'Volume' column
        window: Window size for average volume calculation (default: 20)

    Returns:
        Volume ratio (current / average)
    """
    if len(hist) < window:
        logger.warning(
            f"Insufficient data for volume ratio: {len(hist)} bars, "
            f"need at least {window}"
        )
        return 1.0

    if "Volume" not in hist.columns:
        logger.warning("Volume column not found in DataFrame")
        return 1.0

    current_volume = hist["Volume"].iloc[-1]
    avg_volume = hist["Volume"].iloc[-window:].mean()

    if avg_volume == 0 or pd.isna(avg_volume):
        return 1.0

    return float(current_volume / avg_volume)


def calculate_technical_score(
    hist: pd.DataFrame,
    symbol: str,
    macd_threshold: float = 0.0,
    rsi_overbought: float = 70.0,
    volume_min: float = 0.8,
) -> Tuple[float, dict]:
    """
    Calculate composite technical score for a symbol.

    This function implements the same logic as autonomous_trader.py but
    uses the shared indicator functions.

    Args:
        hist: Historical price DataFrame with 'Close' and 'Volume' columns
        symbol: Symbol name (for logging)
        macd_threshold: Minimum MACD histogram value (default: 0.0)
        rsi_overbought: Maximum RSI value (default: 70.0)
        volume_min: Minimum volume ratio (default: 0.8)

    Returns:
        Tuple of (technical_score, indicators_dict)
        Returns (0, {}) if symbol is rejected by filters
    """
    if hist.empty or len(hist) < 26:
        logger.warning(f"{symbol}: Insufficient data ({len(hist)} bars)")
        return (0.0, {})

    # Calculate indicators
    macd_value, macd_signal, macd_histogram = calculate_macd(hist["Close"])
    rsi_val = calculate_rsi(hist["Close"])
    volume_ratio = calculate_volume_ratio(hist)

    indicators = {
        "macd_value": macd_value,
        "macd_signal": macd_signal,
        "macd_histogram": macd_histogram,
        "rsi": rsi_val,
        "volume_ratio": volume_ratio,
        "current_price": float(hist["Close"].iloc[-1]),
    }

    # HARD FILTERS - Reject entries that don't meet criteria
    if macd_histogram < macd_threshold:
        logger.info(
            f"{symbol}: REJECTED - Bearish MACD histogram ({macd_histogram:.3f})"
        )
        return (0.0, indicators)

    if rsi_val > rsi_overbought:
        logger.info(f"{symbol}: REJECTED - Overbought RSI ({rsi_val:.1f})")
        return (0.0, indicators)

    if volume_ratio < volume_min:
        logger.info(f"{symbol}: REJECTED - Low volume ({volume_ratio:.2f}x)")
        return (0.0, indicators)

    # Calculate composite score (price weighted by technical strength)
    price = hist["Close"].iloc[-1]
    technical_score = (
        price
        * (1 + macd_histogram / 10)
        * (1 + (70 - rsi_val) / 100)
        * volume_ratio
    )

    logger.info(
        f"{symbol}: Score {technical_score:.2f} | "
        f"MACD: {macd_histogram:.3f} | RSI: {rsi_val:.1f} | Vol: {volume_ratio:.2f}x"
    )

    return (technical_score, indicators)


def calculate_atr(
    hist: pd.DataFrame,
    period: int = 14
) -> float:
    """
    Calculate Average True Range (ATR) for dynamic stop-loss placement.
    
    ATR measures market volatility by calculating the average of true ranges
    over a specified period. True Range is the maximum of:
    1. Current High - Current Low
    2. |Current High - Previous Close|
    3. |Current Low - Previous Close|
    
    ATR-based stop-losses adapt to volatility:
    - High volatility = wider stops (less likely to be stopped out by noise)
    - Low volatility = tighter stops (protect profits better)
    
    Args:
        hist: Historical price DataFrame with 'High', 'Low', 'Close' columns
        period: ATR period (default: 14)
    
    Returns:
        ATR value (in price units)
    """
    if len(hist) < period + 1:
        logger.warning(
            f"Insufficient data for ATR calculation: {len(hist)} bars, "
            f"need at least {period + 1}"
        )
        return 0.0
    
    if not all(col in hist.columns for col in ['High', 'Low', 'Close']):
        logger.warning("Missing required columns for ATR: High, Low, Close")
        return 0.0
    
    # Calculate True Range for each period
    high = hist['High']
    low = hist['Low']
    close = hist['Close']
    
    # True Range = max of:
    # 1. High - Low
    # 2. |High - Previous Close|
    # 3. |Low - Previous Close|
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR as simple moving average of True Range
    atr = true_range.rolling(window=period).mean()
    
    # Return most recent value
    atr_value = atr.iloc[-1]
    if pd.isna(atr_value) or atr_value <= 0:
        return 0.0
    
    return float(atr_value)


def calculate_atr_stop_loss(
    entry_price: float,
    atr: float,
    multiplier: float = 2.0,
    direction: str = 'long'
) -> float:
    """
    Calculate ATR-based stop-loss price.
    
    Stop-loss is placed at entry_price ± (multiplier × ATR)
    - Long positions: entry_price - (multiplier × ATR)
    - Short positions: entry_price + (multiplier × ATR)
    
    Common multipliers:
    - 1.5x ATR: Tighter stop (more sensitive)
    - 2.0x ATR: Balanced (default)
    - 2.5x ATR: Wider stop (less sensitive, good for volatile stocks)
    
    Args:
        entry_price: Entry price of the position
        atr: Average True Range value
        multiplier: ATR multiplier (default: 2.0)
        direction: 'long' or 'short' (default: 'long')
    
    Returns:
        Stop-loss price
    """
    if atr <= 0:
        # Fallback to percentage-based stop if ATR unavailable
        if direction == 'long':
            return entry_price * 0.97  # 3% stop-loss
        else:
            return entry_price * 1.03  # 3% stop-loss
    
    stop_distance = multiplier * atr
    
    if direction == 'long':
        stop_price = entry_price - stop_distance
    else:  # short
        stop_price = entry_price + stop_distance
    
    return max(0.0, stop_price)  # Ensure non-negative

