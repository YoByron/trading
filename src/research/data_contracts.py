"""
Data contracts for standardized trading research data structures.

Provides clear schemas for signal snapshots, future returns, and labels
to ensure all models are comparable on the same targets.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


@dataclass
class SignalSnapshot:
    """
    Standardized feature vector at time t.

    This represents all engineered features for a symbol at a specific timestamp.
    """

    timestamp: pd.Timestamp
    symbol: str
    features: pd.Series  # All engineered features
    metadata: dict[str, Any]  # Data source, quality flags, etc.

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "features": self.features.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignalSnapshot":
        """Create from dictionary."""
        return cls(
            timestamp=pd.Timestamp(data["timestamp"]),
            symbol=data["symbol"],
            features=pd.Series(data["features"]),
            metadata=data["metadata"],
        )


@dataclass
class FutureReturns:
    """
    Forward returns over multiple horizons.

    This represents the actual returns that occurred after a signal snapshot.
    """

    symbol: str
    timestamp: pd.Timestamp
    returns_5m: Optional[float] = None
    returns_1h: Optional[float] = None
    returns_1d: Optional[float] = None
    returns_1w: Optional[float] = None
    returns_1mo: Optional[float] = None
    returns_3mo: Optional[float] = None
    realized_vol_1d: Optional[float] = None
    realized_vol_1w: Optional[float] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "returns_5m": self.returns_5m,
            "returns_1h": self.returns_1h,
            "returns_1d": self.returns_1d,
            "returns_1w": self.returns_1w,
            "returns_1mo": self.returns_1mo,
            "returns_3mo": self.returns_3mo,
            "realized_vol_1d": self.realized_vol_1d,
            "realized_vol_1w": self.realized_vol_1w,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FutureReturns":
        """Create from dictionary."""
        return cls(
            symbol=data["symbol"],
            timestamp=pd.Timestamp(data["timestamp"]),
            returns_5m=data.get("returns_5m"),
            returns_1h=data.get("returns_1h"),
            returns_1d=data.get("returns_1d"),
            returns_1w=data.get("returns_1w"),
            returns_1mo=data.get("returns_1mo"),
            returns_3mo=data.get("returns_3mo"),
            realized_vol_1d=data.get("realized_vol_1d"),
            realized_vol_1w=data.get("realized_vol_1w"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Label:
    """
    Supervised learning label.

    Can represent directional (up/down), magnitude (regression), or event-based labels.
    """

    symbol: str
    timestamp: pd.Timestamp
    label_type: str  # 'directional', 'magnitude', 'volatility', 'event'
    value: float  # Label value
    horizon: str  # '5m', '1h', '1d', etc.
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "label_type": self.label_type,
            "value": self.value,
            "horizon": self.horizon,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Label":
        """Create from dictionary."""
        return cls(
            symbol=data["symbol"],
            timestamp=pd.Timestamp(data["timestamp"]),
            label_type=data["label_type"],
            value=data["value"],
            horizon=data["horizon"],
            metadata=data.get("metadata", {}),
        )


def create_signal_snapshot(
    timestamp: pd.Timestamp,
    symbol: str,
    features: pd.Series,
    metadata: Optional[dict[str, Any]] = None,
) -> SignalSnapshot:
    """
    Convenience function to create a SignalSnapshot.

    Args:
        timestamp: Timestamp of the snapshot
        symbol: Symbol name
        features: Feature series
        metadata: Optional metadata

    Returns:
        SignalSnapshot instance
    """
    if metadata is None:
        metadata = {}

    return SignalSnapshot(
        timestamp=timestamp,
        symbol=symbol,
        features=features,
        metadata=metadata,
    )


def create_future_returns(
    symbol: str,
    timestamp: pd.Timestamp,
    returns_data: dict[str, float],
    metadata: Optional[dict[str, Any]] = None,
) -> FutureReturns:
    """
    Convenience function to create FutureReturns.

    Args:
        symbol: Symbol name
        timestamp: Timestamp of the snapshot
        returns_data: Dictionary of returns (e.g., {'1d': 0.02, '1w': 0.05})
        metadata: Optional metadata

    Returns:
        FutureReturns instance
    """
    if metadata is None:
        metadata = {}

    return FutureReturns(
        symbol=symbol,
        timestamp=timestamp,
        returns_1d=returns_data.get("1d"),
        returns_1w=returns_data.get("1w"),
        returns_1mo=returns_data.get("1mo"),
        returns_3mo=returns_data.get("3mo"),
        metadata=metadata,
    )
