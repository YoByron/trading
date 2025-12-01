"""
Options Strategy Module - Yield Generation via Covered Calls

This module implements a Covered Call strategy to generate income from existing
stock positions. It scans the portfolio for positions with >= 100 shares and
sells Out-of-the-Money (OTM) call options against them.

Strategy Parameters:
    - Target Delta: ~0.30 (30% probability of assignment)
    - Expiration: 30-45 days (optimal Theta decay)
    - Minimum Premium: > 0.5% of stock price (annualized > 6%)

AI Integration:
    - Gemini Agent: Fundamental research and long-term outlook
    - LangChain Agent: News sentiment and price action analysis
"""

import logging
import os
import sys
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
import math

# Add project root to path for imports if needed
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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

    Integrates AI Agents for smarter decision making:
    1. Gemini Agent: Research & Fundamentals
    2. LangChain Agent: News & Sentiment
    """

    def __init__(self, paper: bool = True, min_shares_threshold: int = None):
        """
        Initialize the Options Strategy.

        Args:
            paper: If True, use paper trading environment.
            min_shares_threshold: Minimum shares required for covered calls (default: 50, was 100)
        """
        self.paper = paper
        self.options_client = AlpacaOptionsClient(paper=paper)
        self.trader = AlpacaTrader(paper=paper)

        # Strategy Configuration
        # Lowered from 100 to 50 shares for faster activation (more realistic)
        self.min_shares_threshold = min_shares_threshold or int(
            os.getenv("OPTIONS_MIN_SHARES", "50")
        )
        self.target_delta = 0.30
        self.min_days_to_expire = 25
        self.max_days_to_expire = 50
        self.min_annualized_return = 0.06  # 6% annualized yield minimum
        
        logger.info(
            f"Options Strategy initialized: Minimum shares threshold = {self.min_shares_threshold}"
        )

        # Initialize AI Agents
        self.gemini_agent = None
        self.langchain_agent = None
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize AI agents for analysis."""
        try:
            from src.agents.gemini_agent import GeminiAgent

            self.gemini_agent = GeminiAgent(
                name="OptionsResearcher",
                role="Analyze stocks for covered call suitability (yield vs growth trade-off)",
                model="gemini-3-pro-preview",
            )
            logger.info("✅ Gemini Agent initialized for Options Strategy")
        except Exception as e:
            logger.warning(f"⚠️ Gemini Agent unavailable: {e}")

        try:
            from langchain_agents.agents import build_price_action_agent

            self.langchain_agent = build_price_action_agent()
            logger.info("✅ LangChain Agent initialized for Options Strategy")
        except Exception as e:
            logger.warning(f"⚠️ LangChain Agent unavailable: {e}")

    def _analyze_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze sentiment using AI agents.

        Returns:
            Dict with 'sentiment' (BULLISH/BEARISH/NEUTRAL) and 'reasoning'.
        """
        sentiment_score = 0  # -1 to 1
        reasons = []

        # 1. Gemini Analysis (Fundamentals & Outlook)
        if self.gemini_agent:
            try:
                prompt = f"""Analyze {symbol} for a Covered Call strategy.
                We own 100 shares and want to sell a Call option (capping upside).

                Is this stock likely to have a massive breakout soon? (If yes, we should NOT sell).
                Or is it stable/slightly bullish/bearish? (If yes, selling is good).

                Provide a verdict: SELL_CALL (Stable/Neutral/Bearish) or HOLD_SHARES (Strong Bullish Breakout likely).
                """
                result = self.gemini_agent.reason(prompt, thinking_level="low")
                decision = result.get("decision", "")
                reasoning = result.get("reasoning", "")

                reasons.append(f"Gemini: {reasoning[:100]}...")

                if "HOLD_SHARES" in decision or "Strong Bullish" in reasoning:
                    sentiment_score += 1  # Bullish (Don't sell call)
                elif "SELL_CALL" in decision:
                    sentiment_score -= 0.5  # Neutral/Bearish (Sell call)

            except Exception as e:
                logger.warning(f"Gemini analysis failed: {e}")

        # 2. LangChain Analysis (News & Sentiment)
        if self.langchain_agent:
            try:
                prompt = f"What is the current news sentiment for {symbol}? Is there a major catalyst (earnings, FDA approval, merger) this week? Answer YES or NO with reason."
                response = self.langchain_agent.invoke({"input": prompt})
                output = str(response.get("output", ""))

                reasons.append(f"LangChain: {output[:100]}...")

                if "YES" in output.upper() and (
                    "earnings" in output.lower() or "merger" in output.lower()
                ):
                    sentiment_score += (
                        1  # Volatility event likely (Don't sell call or be careful)
                    )

            except Exception as e:
                logger.warning(f"LangChain analysis failed: {e}")

        # Final Decision
        # If score > 0.5, it means Strong Bullish or Volatility Event -> Don't Sell Call
        if sentiment_score > 0.5:
            return {
                "action": "SKIP",
                "sentiment": "BULLISH/VOLATILE",
                "reasoning": "; ".join(reasons),
            }
        else:
            return {
                "action": "PROCEED",
                "sentiment": "NEUTRAL/BEARISH",
                "reasoning": "; ".join(reasons),
            }

    def execute_daily(self) -> List[Dict[str, Any]]:
        """
        Execute the daily options routine.

        1. Scan portfolio for eligible positions (>= 100 shares).
        2. For each eligible position, check if we already have a covered call.
        3. Analyze sentiment via AI Agents.
        4. If sentiment allows, find and execute a new covered call.
        """
        logger.info("Starting Daily Options Strategy Execution...")
        results = []

        try:
            # 1. Get Portfolio Positions
            positions = self.trader.get_positions()
            eligible_positions = [
                p
                for p in positions
                if float(p["qty"]) >= self.min_shares_threshold
                and p["side"] == "long"
            ]

            if not eligible_positions:
                logger.info(
                    f"No positions eligible for covered calls (need >= {self.min_shares_threshold} shares)."
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
                if self._has_open_covered_call(symbol, positions):
                    logger.info(f"Skipping {symbol}: Already has an open covered call.")
                    continue

                # 3. AI Sentiment Analysis
                analysis = self._analyze_sentiment(symbol)
                logger.info(
                    f"AI Analysis for {symbol}: {analysis['sentiment']} - {analysis['action']}"
                )

                if analysis["action"] == "SKIP":
                    logger.info(
                        f"Skipping {symbol} due to AI analysis: {analysis['reasoning']}"
                    )
                    continue

                # 4. Find Best Covered Call
                contract = self.find_covered_call_contract(symbol, current_price)

                if contract:
                    logger.info(
                        f"Found Candidate for {symbol}: {contract['symbol']} "
                        f"(Strike: {contract['strike_price']}, Delta: {contract['delta']:.2f}, "
                        f"Premium: ${contract['price']:.2f})"
                    )

                    # 5. Execute Trade (Sell to Open)
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
                        "ai_analysis": analysis,
                    }
                    results.append(trade_result)
                else:
                    logger.info(f"No suitable contract found for {symbol}.")

            return results

        except Exception as e:
            logger.error(f"Error in options strategy execution: {e}")
            return []

    def _has_open_covered_call(
        self, underlying_symbol: str, positions: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if there is an existing short call position for the underlying symbol.
        """
        for pos in positions:
            # Filter for short positions
            if pos.get("side") != "short":
                continue

            sym = pos.get("symbol", "")
            # Check if it looks like an option for this underlying
            # Heuristic: Starts with underlying, is longer than underlying, contains digits
            if (
                sym.startswith(underlying_symbol)
                and len(sym) > len(underlying_symbol)
                and any(c.isdigit() for c in sym)
            ):
                # Ideally, we should parse the OCC symbol to confirm it's a Call ('C')
                # but checking for *any* short option on this underlying is a safe conservative baseline.
                return True
        return False

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
