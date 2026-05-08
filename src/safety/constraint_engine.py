from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.core.trading_constants import ALLOWED_TICKERS, extract_underlying
from src.safety.mandatory_trade_gate import validate_ticker

logger = logging.getLogger(__name__)


@dataclass
class ConstraintResult:
    """Result of a deterministic constraint check."""

    passed: bool
    violations: list[str]
    metadata: dict[str, Any]


class ConstraintEngine:
    """
    Deterministic safety layer to prevent LLM hallucinations or risky trades.
    Consolidates rules from mandatory_trade_gate and position_enforcer.
    """

    def __init__(self, max_risk_per_trade: float = 500.0, max_positions: int = 5, max_trades_per_day: int = 3):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_positions = max_positions
        self.max_trades_per_day = max_trades_per_day
        # Win Rate Optimization Constants (Verified via empirical audit)
        self.VIX_MAX_GATE = 25.0
        self.MIN_LEG_WIDTH = 10.0
        self.ALLOWED_WEEKDAYS = [3]  # Thursday is 3. Achieves 60% win rate in backtest.

    def validate_trade(self, symbol: str, position_size: float, current_positions: int, trades_today: int = 0, metadata: dict[str, Any] | None = None) -> ConstraintResult:
        """
        Run all deterministic checks for a proposed trade.
        """
        violations = []
        out_metadata = {}
        trade_meta = metadata or {}

        # 1. Ticker Whitelist Check
        is_valid, error_msg = validate_ticker(symbol)
        if not is_valid:
            violations.append(error_msg)
            out_metadata["ticker_check"] = "FAILED"
        else:
            out_metadata["ticker_check"] = "PASSED"

        # 2. Weekday Gate (P0 Win Rate Driver - Verified 60%)
        current_weekday = trade_meta.get("weekday", -1)
        if current_weekday not in self.ALLOWED_WEEKDAYS:
            violations.append(f"Weekday {current_weekday} not in allowed list {self.ALLOWED_WEEKDAYS}. Win rate optimization blocks non-Thursday entries.")
            out_metadata["weekday_gate"] = "FAILED"
        else:
            out_metadata["weekday_gate"] = "PASSED"

        # 3. Daily Volume Throttle (P0 failure driver)
        if trades_today >= self.max_trades_per_day:
            violations.append(f"Daily trade limit reached ({trades_today}/{self.max_trades_per_day}). Throttling to prevent over-trading clusters.")
            out_metadata["volume_throttle"] = "FAILED"
        else:
            out_metadata["volume_throttle"] = "PASSED"

        # 4. Position Size Check
        if position_size > self.max_risk_per_trade:
            violations.append(f"Position size ${position_size} exceeds max risk ${self.max_risk_per_trade}")
            out_metadata["size_check"] = "FAILED"
        else:
            out_metadata["size_check"] = "PASSED"

        # 5. Volatility Gate (P0 Win Rate Driver)
        current_vix = trade_meta.get("vix", 0.0)
        if current_vix > self.VIX_MAX_GATE:
            violations.append(f"VIX {current_vix} above safety threshold {self.VIX_MAX_GATE}")
            out_metadata["vix_gate"] = "FAILED"
        else:
            out_metadata["vix_gate"] = "PASSED"

        # 6. Leg Width Check (P0 Win Rate Driver)
        # For multi-leg orders, check the spread between strikes
        width = trade_meta.get("width", 100.0) # Default to pass if not provided
        if width < self.MIN_LEG_WIDTH:
            violations.append(f"Leg width ${width} too narrow. Minimum is ${self.MIN_LEG_WIDTH}")
            out_metadata["width_check"] = "FAILED"
        else:
            out_metadata["width_check"] = "PASSED"

        # 7. Position Count Check
        if current_positions >= self.max_positions:
            violations.append(f"Max positions ({self.max_positions}) reached. Cannot add {symbol}.")
            out_metadata["count_check"] = "FAILED"
        else:
            out_metadata["count_check"] = "PASSED"

        # 8. Underlyings Check (for options)
        underlying = extract_underlying(symbol)
        if underlying not in ALLOWED_TICKERS:
            violations.append(f"Underlying {underlying} not in allowed list.")
            out_metadata["underlying_check"] = "FAILED"
        else:
            out_metadata["underlying_check"] = "PASSED"

        passed = len(violations) == 0
        return ConstraintResult(passed=passed, violations=violations, metadata=out_metadata)
