"""
Canonical baseline strategies for benchmarking.

Provides standard baseline strategies so you always know if a new idea
beats trivial strategies:
- Buy-and-hold
- Equal-weight portfolio
- Simple moving-average cross (SMA 50/200)
- Time-series momentum (1-month, 3-month, 6-month)
- Cross-sectional momentum (rank-based)
- Mean-reversion (RSI-based)
"""

from src.research.baselines.buy_and_hold import BuyAndHoldStrategy
from src.research.baselines.equal_weight import EqualWeightStrategy
from src.research.baselines.momentum import MomentumStrategy
from src.research.baselines.sma_cross import SMACrossStrategy

__all__ = [
    "BuyAndHoldStrategy",
    "EqualWeightStrategy",
    "MomentumStrategy",
    "SMACrossStrategy",
]
