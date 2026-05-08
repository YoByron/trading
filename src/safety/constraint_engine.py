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

    def __init__(self, max_risk_per_trade: float = 500.0, max_positions: int = 5):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_positions = max_positions

    def validate_trade(self, symbol: str, position_size: float, current_positions: int) -> ConstraintResult:
        """
        Run all deterministic checks for a proposed trade.
        """
        violations = []
        metadata = {}

        # 1. Ticker Whitelist Check
        is_valid, error_msg = validate_ticker(symbol)
        if not is_valid:
            violations.append(error_msg)
            metadata["ticker_check"] = "FAILED"
        else:
            metadata["ticker_check"] = "PASSED"

        # 2. Position Size Check
        # Hard limit of $500 risk per trade for now (0.5% of $100K)
        if position_size > self.max_risk_per_trade:
            violations.append(f"Position size ${position_size} exceeds max risk ${self.max_risk_per_trade}")
            metadata["size_check"] = "FAILED"
        else:
            metadata["size_check"] = "PASSED"

        # 3. Position Count Check
        if current_positions >= self.max_positions:
            violations.append(f"Max positions ({self.max_positions}) reached. Cannot add {symbol}.")
            metadata["count_check"] = "FAILED"
        else:
            metadata["count_check"] = "PASSED"

        # 4. Underlyings Check (for options)
        underlying = extract_underlying(symbol)
        if underlying not in ALLOWED_TICKERS:
            violations.append(f"Underlying {underlying} not in allowed list.")
            metadata["underlying_check"] = "FAILED"
        else:
            metadata["underlying_check"] = "PASSED"

        passed = len(violations) == 0
        return ConstraintResult(passed=passed, violations=violations, metadata=metadata)
