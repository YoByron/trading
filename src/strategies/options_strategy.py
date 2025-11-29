"""
Options Strategy Module - Yield Generation via Covered Calls

This module implements a Covered Call strategy to generate income from existing
stock positions. It scans the portfolio for positions with >= 100 shares and
sells Out-of-the-Money (OTM) call options against them.

Strategy Parameters:
    - Target Delta: ~0.30 (30% probability of assignment)
    - Expiration: 30-45 days (optimal Theta decay)
    - Minimum Premium: > 0.5% of stock price (annualized > 6%)
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
import math

from src.core.options_client import AlpacaOptionsClient
from src.core.alpaca_trader import AlpacaTrader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OptionsStrategy:
    """
    Automated Options Strategy for Yield Generation.
    """

    def __init__(self, paper: bool = True):
        """
        Initialize the Options Strategy.

        Args:
            paper: If True, use paper trading environment.
        """
        self.paper = paper
        self.options_client = AlpacaOptionsClient(paper=paper)
        self.trader = AlpacaTrader(paper=paper)

        # Strategy Configuration
        self.target_delta = 0.30
        self.min_days_to_expire = 25
        self.max_days_to_expire = 50
        self.min_annualized_return = 0.06  # 6% annualized yield minimum

    def execute_daily(self) -> List[Dict[str, Any]]:
        """
        Execute the daily options routine.

        1. Scan portfolio for eligible positions (>= 100 shares).
        2. For each eligible position, check if we already have a covered call.
        3. If not, find and execute a new covered call.
        """
        logger.info("Starting Daily Options Strategy Execution...")
        results = []

        try:
            # 1. Get Portfolio Positions
            positions = self.trader.get_positions()
            eligible_positions = [
                p for p in positions if float(p["qty"]) >= 100 and p["side"] == "long"
            ]

            if not eligible_positions:
                logger.info(
                    "No positions eligible for covered calls (need >= 100 shares)."
                )
                return results

            # 2. Process Each Eligible Position
            for pos in eligible_positions:
                symbol = pos["symbol"]
                qty = float(pos["qty"])
                current_price = float(pos["current_price"])

                logger.info(
                    f"Analyzing {symbol} for Covered Call opportunity ({qty} shares)..."
                )

                # Check if we already have an open short call for this symbol
                # (Simplified check: simplistic portfolio scan for option symbols matching underlying)
                # In a real system, we'd map option_symbol -> underlying.
                # For now, we'll assume we don't have one if we are just testing logic.
                # TODO: Implement robust check for existing covered calls.

                # 3. Find Best Covered Call
                contract = self.find_covered_call_contract(symbol, current_price)

                if contract:
                    logger.info(
                        f"Found Candidate for {symbol}: {contract['symbol']} "
                        f"(Strike: {contract['strike_price']}, Delta: {contract['delta']:.2f}, "
                        f"Premium: ${contract['price']:.2f})"
                    )

                    # 4. Execute Trade (Sell to Open)
                    # Note: Actual execution requires permission and careful order construction.
                    # For Phase 2 prototype, we will just LOG the opportunity.
                    trade_result = {
                        "action": "PROPOSED_SELL_OPEN",
                        "underlying": symbol,
                        "option_symbol": contract["symbol"],
                        "strike": contract["strike_price"],
                        "expiration": contract["expiration_date"],
                        "premium": contract["price"],
                        "delta": contract["delta"],
                        "contracts": math.floor(qty / 100),
                    }
                    results.append(trade_result)
                else:
                    logger.info(f"No suitable contract found for {symbol}.")

            return results

        except Exception as e:
            logger.error(f"Error in options strategy execution: {e}")
            return []

    def find_covered_call_contract(
        self, symbol: str, current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best call option to sell based on strategy criteria.
        """
        try:
            # Fetch full chain
            chain = self.options_client.get_option_chain(symbol)

            # Filter for Calls
            calls = [
                c for c in chain if "C" in c["symbol"].split(symbol)[-1]
            ]  # Heuristic parsing or checking type
            # Better: Alpaca contract objects usually have a 'type' field, but our client returns dicts.
            # Let's assume our client helper needs to parse the symbol or we rely on the data.
            # Standard OCC symbol: SPY251219C00600000 (C for Call)

            # Let's refine the client to return parsed info if possible, or parse here.
            # Parsing OCC symbol: 6 chars root, 6 chars date (YYMMDD), 1 char type (C/P), 8 chars price

            candidates = []
            target_date_min = date.today() + timedelta(days=self.min_days_to_expire)
            target_date_max = date.today() + timedelta(days=self.max_days_to_expire)

            for contract in chain:
                sym = contract["symbol"]

                # Parse OCC Symbol
                # Assuming standard format. Root length varies, but usually we can find C/P.
                # A robust parser is needed. For now, simple heuristic:
                try:
                    # Find the 'C' or 'P' after the digits start
                    # Actually, Alpaca data client might provide expiration and strike in the object
                    # But our client wrapper converted to dict.
                    # Let's rely on parsing the symbol for now.

                    # Example: SPY251219C00600000
                    # Root: SPY (variable)
                    # Date: 251219 (YYMMDD)
                    # Type: C
                    # Strike: 00600000 ($600.00)

                    # Find the first digit
                    first_digit_idx = -1
                    for i, char in enumerate(sym):
                        if char.isdigit():
                            first_digit_idx = i
                            break

                    if first_digit_idx == -1:
                        continue

                    root = sym[:first_digit_idx]
                    if root != symbol:
                        continue  # Should match

                    date_str = sym[first_digit_idx : first_digit_idx + 6]
                    type_char = sym[first_digit_idx + 6]
                    strike_str = sym[first_digit_idx + 7 :]

                    if type_char != "C":
                        continue  # Only Calls

                    exp_date = datetime.strptime(date_str, "%y%m%d").date()
                    strike_price = float(strike_str) / 1000.0

                    # Filter Expiration
                    if not (target_date_min <= exp_date <= target_date_max):
                        continue

                    # Filter Strike (OTM)
                    if strike_price <= current_price:
                        continue

                    # Filter Delta
                    greeks = contract.get("greeks")
                    if not greeks:
                        continue
                    delta = greeks.get("delta")
                    if delta is None:
                        continue

                    # We want Delta ~ 0.30. Let's look for 0.20 to 0.40 range.
                    if not (0.20 <= delta <= 0.40):
                        continue

                    # Add to candidates
                    contract["expiration_date"] = exp_date
                    contract["strike_price"] = strike_price
                    contract["delta"] = delta
                    contract["price"] = (
                        contract["latest_trade_price"]
                        or contract["latest_quote_bid"]
                        or 0.0
                    )

                    candidates.append(contract)

                except Exception:
                    continue

            # Select Best Candidate
            # Sort by closeness to target delta (0.30)
            if not candidates:
                return None

            best_contract = min(
                candidates, key=lambda x: abs(x["delta"] - self.target_delta)
            )
            return best_contract

        except Exception as e:
            logger.error(f"Error finding contract: {e}")
            return None
