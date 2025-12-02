"""
Factor/feature libraries for trading strategy research.

This module provides standardized feature engineering functions:
- Returns: Multi-horizon returns (1m, 5m, 1h, 1d, 1w)
- Volatility: Realized vol, GARCH, regime-conditional vol
- Volume/Flow: Volume profile, order flow imbalance, VWAP deviations
- Technicals: Standardized technical indicators (RSI, MACD, Bollinger)
- Cross-sectional: Rank-based features (percentile ranks, z-scores)
- Microstructure: Bid-ask spread, order book depth (if available)
- Regime: Market regime indicators (HMM, volatility regimes)
"""

"""
Factor/feature libraries for trading strategy research.

This module provides standardized feature engineering functions.
"""

from src.research.factors.cross_sectional import (
    calculate_cross_sectional_mean_reversion,
    calculate_cross_sectional_momentum,
    calculate_percentile_ranks,
    calculate_relative_strength,
    calculate_z_scores,
)
from src.research.factors.returns import (
    calculate_cumulative_returns,
    calculate_multi_horizon_returns,
    calculate_returns,
    calculate_rolling_returns,
)
from src.research.factors.technicals import (
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    calculate_stochastic,
    calculate_technical_indicators,
)
from src.research.factors.volatility import (
    calculate_atr_volatility,
    calculate_garch_volatility,
    calculate_realized_volatility,
    calculate_regime_conditional_volatility,
)
from src.research.factors.volume_flow import (
    calculate_obv,
    calculate_volume_price_trend,
    calculate_volume_profile,
    calculate_volume_ratio,
    calculate_volume_weighted_returns,
    calculate_vwap_deviation,
)

__all__ = [
    # Returns
    "calculate_returns",
    "calculate_multi_horizon_returns",
    "calculate_cumulative_returns",
    "calculate_rolling_returns",
    # Volatility
    "calculate_realized_volatility",
    "calculate_garch_volatility",
    "calculate_regime_conditional_volatility",
    "calculate_atr_volatility",
    # Volume/Flow
    "calculate_volume_profile",
    "calculate_vwap_deviation",
    "calculate_volume_ratio",
    "calculate_volume_weighted_returns",
    "calculate_obv",
    "calculate_volume_price_trend",
    # Technicals
    "calculate_technical_indicators",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "calculate_sma",
    "calculate_ema",
    "calculate_stochastic",
    # Cross-sectional
    "calculate_percentile_ranks",
    "calculate_z_scores",
    "calculate_cross_sectional_momentum",
    "calculate_cross_sectional_mean_reversion",
    "calculate_relative_strength",
]
