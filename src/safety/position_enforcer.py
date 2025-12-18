"""
Position Enforcer - Closes Positions That Violate Lessons Learned

This runs BEFORE trading starts each day and:
1. Reads ALL lessons learned from RAG
2. Extracts BANNED symbols/strategies
3. Checks actual portfolio positions
4. CLOSES any positions that violate lessons

Created: Dec 17, 2025
Purpose: ENFORCE lessons, not just warn about them

Example violations:
- Lesson says "crypto removed" → Close BTCUSD, ETHUSD, SOLUSD
- Lesson says "REIT disabled" → Close AMT, CCI, DLR, EQIX, PSA
- Lesson says "symbol X banned" → Close X
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ViolatingPosition:
    """A position that violates a lesson learned."""

    symbol: str
    quantity: float
    value: float
    lesson_file: str
    violation_reason: str
    unrealized_pl: float = 0.0


@dataclass
class EnforcementResult:
    """Result of position enforcement."""

    violations_found: int
    positions_closed: int
    total_value_closed: float
    errors: list[str]
    closed_symbols: list[str]
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "violations_found": self.violations_found,
            "positions_closed": self.positions_closed,
            "total_value_closed": self.total_value_closed,
            "errors": self.errors,
            "closed_symbols": self.closed_symbols,
            "timestamp": self.timestamp,
        }


class PositionEnforcer:
    """
    Enforces lessons learned by closing positions that violate them.

    This is the MISSING piece that makes RAG actually work:
    - Trade gate blocks NEW trades ✓
    - Position enforcer closes OLD positions ✓
    """

    def __init__(self, alpaca_trader=None):
        self.alpaca_trader = alpaca_trader
        self.lessons_dir = Path("rag_knowledge/lessons_learned")
        self.enabled = os.getenv("POSITION_ENFORCER_ENABLED", "true").lower() in {"1", "true", "yes"}

        # Banned patterns we extract from lessons
        self.banned_symbols: set[str] = set()
        self.banned_patterns: set[str] = set()
        self.banned_strategies: set[str] = set()

        logger.info(f"PositionEnforcer initialized (enabled={self.enabled})")

    def _extract_bans_from_lessons(self) -> None:
        """
        Read ALL lessons and extract what's banned.

        Looks for patterns like:
        - "crypto removed", "crypto disabled", "NO crypto"
        - "REIT disabled", "disable REIT"
        - "symbol X banned"
        - Lists of tickers to avoid
        """
        if not self.lessons_dir.exists():
            logger.warning(f"Lessons directory not found: {self.lessons_dir}")
            return

        logger.info(f"📚 Reading lessons from {self.lessons_dir}")

        for lesson_file in self.lessons_dir.glob("*.md"):
            try:
                content = lesson_file.read_text()
                content_lower = content.lower()

                # ========== CRYPTO BANS ==========
                crypto_ban_patterns = [
                    "crypto removed",
                    "crypto disabled",
                    "crypto trading disabled",
                    "no crypto",
                    "remove crypto",
                    "disable crypto",
                    "crypto strategy removed",
                    "0% win rate, -$",  # Specific to crypto lesson
                ]

                for pattern in crypto_ban_patterns:
                    if pattern in content_lower:
                        logger.info(f"🚫 Found crypto ban in {lesson_file.name}")
                        self.banned_patterns.add("crypto")
                        self.banned_symbols.update(["BTCUSD", "ETHUSD", "SOLUSD", "BTC/USD", "ETH/USD", "SOL/USD"])
                        break

                # ========== REIT BANS ==========
                reit_ban_patterns = [
                    "reit disabled",
                    "disable reit",
                    "reit allocation: 0",
                    "reit_allocation_pct: '0'",
                ]

                for pattern in reit_ban_patterns:
                    if pattern in content_lower:
                        logger.info(f"🚫 Found REIT ban in {lesson_file.name}")
                        self.banned_patterns.add("reit")
                        # Extract REIT symbols from lesson
                        reit_symbols = re.findall(r'\b(AMT|CCI|DLR|EQIX|PLD|PSA|VICI|O|WELL|AVB|EQR|INVH)\b', content)
                        self.banned_symbols.update(reit_symbols)
                        break

                # ========== SPECIFIC SYMBOL BANS ==========
                # Look for "symbol X banned" or "never trade X"
                symbol_ban_match = re.findall(r'(?:ban|avoid|never trade|remove)\s+([A-Z]{2,5})', content)
                if symbol_ban_match:
                    for symbol in symbol_ban_match:
                        if len(symbol) <= 5:  # Valid ticker
                            logger.info(f"🚫 Found symbol ban: {symbol} in {lesson_file.name}")
                            self.banned_symbols.add(symbol)

                # ========== STRATEGY BANS ==========
                if "tier5" in content_lower and ("disabled" in content_lower or "removed" in content_lower):
                    self.banned_strategies.add("tier5")
                    self.banned_strategies.add("crypto")

                if "tier7" in content_lower and ("disabled" in content_lower or "removed" in content_lower):
                    self.banned_strategies.add("tier7")
                    self.banned_strategies.add("reit")

            except Exception as e:
                logger.error(f"Error reading lesson {lesson_file.name}: {e}")

        logger.info("📋 Extracted bans:")
        logger.info(f"   Banned symbols: {sorted(self.banned_symbols)}")
        logger.info(f"   Banned patterns: {sorted(self.banned_patterns)}")
        logger.info(f"   Banned strategies: {sorted(self.banned_strategies)}")

    def _check_position_violations(self) -> list[ViolatingPosition]:
        """
        Check actual portfolio positions against banned list.

        Returns list of positions that violate lessons.
        """
        violations = []

        if not self.alpaca_trader:
            logger.warning("No Alpaca trader provided - cannot check positions")
            return violations

        try:
            # Get all positions
            positions = self.alpaca_trader.get_positions()

            if not positions:
                logger.info("✓ No positions to check")
                return violations

            logger.info(f"🔍 Checking {len(positions)} positions for violations")

            for position in positions:
                symbol = position.symbol
                qty = float(position.qty)
                value = float(position.market_value)
                unrealized_pl = float(position.unrealized_pl)

                # Check if symbol is banned
                if symbol in self.banned_symbols:
                    violations.append(ViolatingPosition(
                        symbol=symbol,
                        quantity=qty,
                        value=value,
                        lesson_file="extracted from lessons",
                        violation_reason=f"Symbol {symbol} is banned",
                        unrealized_pl=unrealized_pl,
                    ))
                    logger.warning(f"🚨 VIOLATION: {symbol} position exists but is BANNED")

                # Check if matches banned pattern
                symbol_lower = symbol.lower()
                for pattern in self.banned_patterns:
                    if pattern in symbol_lower:
                        violations.append(ViolatingPosition(
                            symbol=symbol,
                            quantity=qty,
                            value=value,
                            lesson_file="extracted from lessons",
                            violation_reason=f"Symbol matches banned pattern: {pattern}",
                            unrealized_pl=unrealized_pl,
                        ))
                        logger.warning(f"🚨 VIOLATION: {symbol} matches banned pattern '{pattern}'")
                        break

        except Exception as e:
            logger.error(f"Error checking positions: {e}")

        return violations

    def _close_violating_position(self, violation: ViolatingPosition) -> bool:
        """
        Close a position that violates lessons.

        Returns True if successfully closed, False otherwise.
        """
        if not self.alpaca_trader:
            logger.error("Cannot close position - no Alpaca trader")
            return False

        try:
            symbol = violation.symbol
            qty = abs(violation.quantity)

            logger.info(f"🔥 CLOSING VIOLATION: {symbol} (qty={qty}, value=${violation.value:.2f}, P/L=${violation.unrealized_pl:.2f})")
            logger.info(f"   Reason: {violation.violation_reason}")

            # Determine side (SELL for long, BUY for short)
            side = "SELL" if violation.quantity > 0 else "BUY"

            # Submit market order to close
            from alpaca.trading.enums import OrderSide, TimeInForce
            from alpaca.trading.requests import MarketOrderRequest

            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL if side == "SELL" else OrderSide.BUY,
                time_in_force=TimeInForce.GTC
            )

            order = self.alpaca_trader.trading_client.submit_order(order_data=order_data)
            logger.info(f"   ✅ Order submitted: {order.id}")

            return True

        except Exception as e:
            logger.error(f"Failed to close {violation.symbol}: {e}")
            return False

    def enforce(self) -> EnforcementResult:
        """
        Main enforcement method - run this before trading starts.

        Returns:
            EnforcementResult with details of what was closed
        """
        if not self.enabled:
            logger.info("Position enforcer is DISABLED")
            return EnforcementResult(
                violations_found=0,
                positions_closed=0,
                total_value_closed=0.0,
                errors=["Enforcer disabled"],
                closed_symbols=[],
                timestamp=datetime.now().isoformat(),
            )

        logger.info("=" * 80)
        logger.info("POSITION ENFORCER - Checking for violations of lessons learned")
        logger.info("=" * 80)

        # Step 1: Extract bans from lessons
        self._extract_bans_from_lessons()

        # Step 2: Check positions
        violations = self._check_position_violations()

        if not violations:
            logger.info("✅ No violations found - all positions comply with lessons")
            return EnforcementResult(
                violations_found=0,
                positions_closed=0,
                total_value_closed=0.0,
                errors=[],
                closed_symbols=[],
                timestamp=datetime.now().isoformat(),
            )

        # Step 3: Close violations
        logger.warning(f"🚨 Found {len(violations)} positions that violate lessons")

        closed_count = 0
        total_value = 0.0
        errors = []
        closed_symbols = []

        for violation in violations:
            success = self._close_violating_position(violation)
            if success:
                closed_count += 1
                total_value += violation.value
                closed_symbols.append(violation.symbol)
            else:
                errors.append(f"Failed to close {violation.symbol}")

        result = EnforcementResult(
            violations_found=len(violations),
            positions_closed=closed_count,
            total_value_closed=total_value,
            errors=errors,
            closed_symbols=closed_symbols,
            timestamp=datetime.now().isoformat(),
        )

        logger.info("=" * 80)
        logger.info("ENFORCEMENT COMPLETE:")
        logger.info(f"  Violations found: {result.violations_found}")
        logger.info(f"  Positions closed: {result.positions_closed}")
        logger.info(f"  Total value closed: ${result.total_value_closed:.2f}")
        logger.info(f"  Closed symbols: {result.closed_symbols}")
        if result.errors:
            logger.error(f"  Errors: {result.errors}")
        logger.info("=" * 80)

        return result


# Convenience function
def enforce_positions(alpaca_trader=None) -> EnforcementResult:
    """
    Quick way to run position enforcement.

    Usage:
        from src.safety.position_enforcer import enforce_positions
        result = enforce_positions(trader)
        if result.violations_found > 0:
            logger.warning(f"Closed {result.positions_closed} violating positions")
    """
    enforcer = PositionEnforcer(alpaca_trader=alpaca_trader)
    return enforcer.enforce()
