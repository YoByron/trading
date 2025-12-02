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

# Import all factor modules
try:
    from src.research.factors.returns import (
        calculate_returns,
        calculate_multi_horizon_returns,
    )
    from src.research.factors.volatility import (
        calculate_realized_volatility,
        calculate_garch_volatility,
    )
    from src.research.factors.volume_flow import (
        calculate_volume_profile,
        calculate_vwap_deviation,
    )
    from src.research.factors.technicals import (
        calculate_technical_indicators,
    )
    from src.research.factors.cross_sectional import (
        calculate_percentile_ranks,
        calculate_z_scores,
    )

    __all__ = [
        "calculate_returns",
        "calculate_multi_horizon_returns",
        "calculate_realized_volatility",
        "calculate_garch_volatility",
        "calculate_volume_profile",
        "calculate_vwap_deviation",
        "calculate_technical_indicators",
        "calculate_percentile_ranks",
        "calculate_z_scores",
    ]
except ImportError:
    # Graceful fallback if modules aren't available
    __all__ = []
