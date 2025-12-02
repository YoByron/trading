"""
Portfolio optimization and construction module.

Provides position sizing algorithms and portfolio construction methods:
- Mean-variance optimization (Markowitz)
- Risk parity (equal risk contribution)
- Hierarchical Risk Parity (HRP)
- Kelly Criterion sizing
- Volatility scaling
- Constraints: sector caps, concentration limits, turnover
"""

from src.research.portfolio.optimizer import (
    PortfolioOptimizer,
    OptimizationMethod,
    PortfolioConstraints,
    OptimizationResult,
)
from src.research.portfolio.risk_parity import (
    calculate_risk_parity_weights,
    calculate_equal_risk_contribution,
)
from src.research.portfolio.kelly import (
    calculate_kelly_fraction,
    calculate_half_kelly,
)

__all__ = [
    "PortfolioOptimizer",
    "OptimizationMethod",
    "PortfolioConstraints",
    "OptimizationResult",
    "calculate_risk_parity_weights",
    "calculate_equal_risk_contribution",
    "calculate_kelly_fraction",
    "calculate_half_kelly",
]
