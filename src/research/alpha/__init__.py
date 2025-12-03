"""
Alpha research and signal generation.

Provides tools for alpha signal development:
- Feature library with common features
- Signal generation and ranking
- Information Coefficient analysis
- Alpha combination methods
"""

from src.research.alpha.features import (
    FeatureLibrary,
    compute_momentum_features,
    compute_technical_features,
    compute_volatility_features,
    compute_volume_features,
)
from src.research.alpha.signals import (
    AlphaSignal,
    SignalGenerator,
    combine_signals,
    rank_signals_by_ic,
)

__all__ = [
    "FeatureLibrary",
    "compute_momentum_features",
    "compute_volatility_features",
    "compute_volume_features",
    "compute_technical_features",
    "AlphaSignal",
    "SignalGenerator",
    "combine_signals",
    "rank_signals_by_ic",
]
