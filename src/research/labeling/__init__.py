"""
Labeling pipeline for supervised learning targets.

Provides reusable functions to create supervised learning targets:
- Directional labels (up/down) over multiple horizons
- Volatility/realized variance labels
- Event-based labels (triple-barrier method)
"""

from src.research.labeling.directional import create_directional_labels
from src.research.labeling.triple_barrier import create_triple_barrier_labels
from src.research.labeling.volatility import create_volatility_labels

__all__ = [
    "create_directional_labels",
    "create_volatility_labels",
    "create_triple_barrier_labels",
]
