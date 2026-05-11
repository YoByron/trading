"""
Execution Agent: Order execution and timing optimization

Responsibilities:
- Execute orders via Alpaca API
- Optimize execution timing
- Handle order failures
- Track execution quality

Ensures best execution
"""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from typing import Any

from alpaca.trading.client import TradingClient

try:
    from src.core.options_client import AlpacaOptionsClient
except Exception:  # pragma: no cover - optional dependency in lightweight test envs
    AlpacaOptionsClient = None  # type: ignore[misc,assignment]

from src.resilience.audit_graph import AuditGraph
from src.safety.constraint_engine import ConstraintEngine
from src.schemas.events import AuditEvent, EventType
from src.utils.market_data import MarketDataProvider
from src.utils.technical_indicators import calculate_macd, calculate_rsi

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ExecutionAgent(BaseAgent):
    """
    Agent responsible for executing trades efficiently.

    Responsibilities:
    - Execute orders with minimal slippage
    - Monitor order status
    - Handle partial fills
    - Track execution quality (slippage, fill rate)
    """

    def __init__(
        self,
        alpaca_api: TradingClient | None = None,
        *,
        paper: bool = True,
        options_client: AlpacaOptionsClient | None = None,
    ):
        super().__init__(name="ExecutionAgent", role="Order execution and timing optimization")
        self.alpaca_api = alpaca_api
        self.paper = paper
        self.options_client = options_client
        self.execution_history: list = []
        # Lazily instantiated options client (False sentinel == permanently unavailable)
        self._options_client: AlpacaOptionsClient | None | bool = options_client
        self.data_provider = MarketDataProvider()
        self.audit_graph = AuditGraph()
        self.constraint_engine = ConstraintEngine()

    def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze execution timing and prepare order.

        Args:
            data: Contains action, symbol, position_size, market conditions

        Returns:
            Execution plan with timing recommendation
        """
        trace_id = data.get("trace_id", str(uuid.uuid4()))
        action = data.get("action", "HOLD")
        symbol = data.get("symbol", "UNKNOWN")
        position_size = data.get("position_size", 0)
        market_conditions = data.get("market_conditions", {})

        # Emit Signal Event
        self.audit_graph.emit(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                trace_id=trace_id,
                event_type=EventType.SIGNAL,
                agent_id=self.name,
                data={"symbol": symbol, "action": action, "size": position_size},
            )
        )

        if action == "HOLD":
            return {"action": "NO_EXECUTION", "reasoning": "HOLD recommendation - no order needed", "trace_id": trace_id}

        # Check market status
        market_status = self._check_market_status()

        # FETCH HISTORICAL DATA AND CALCULATE TECHNICALS
        macd_hist = 0.0
        rsi = 50.0
        try:
            # Fetch 60 days of data to ensure enough for MACD/RSI
            hist_result = self.data_provider.get_daily_bars(symbol, lookback_days=60)
            if not hist_result.data.empty:
                prices = hist_result.data["Close"]
                _, _, macd_hist = calculate_macd(prices)
                rsi = calculate_rsi(prices)
        except Exception as e:
            logger.warning(f"Failed to calculate technicals for {symbol}: {e}")

        # Build execution analysis prompt
        memory_context = self.get_memory_context(limit=10)

        # Goldilocks Prompt: Focused execution with timing examples
        prompt = f"""Execute {action} ${position_size:,.0f} on {symbol}. Minimize slippage, maximize fill quality.

ORDER: {action} {symbol} ${position_size:,.0f} (Market) | Status: {market_status["status"]}
CONDITIONS: Spread {market_conditions.get("spread", "N/A")} | Vol {market_conditions.get("volume", "N/A")} | Volatility {market_conditions.get("volatility", "N/A")}
TECHNICALS: MACD Hist {macd_hist:.3f} | RSI {rsi:.1f}

{memory_context}

REASONING PROTOCOL:
Think step-by-step before deciding:
1. Check market status and timing constraints
2. Evaluate liquidity conditions (spread, volume)
3. Assess technical momentum (RSI, MACD)
4. Estimate slippage risk based on conditions
5. Critique your assessment - what execution risk are you underestimating?

PRINCIPLES:
- Wide spread (>0.1%) = wait for better liquidity or use limit order
- Low volume (<50% avg) = expect higher slippage, consider splitting
- First/last 15 min of day = higher volatility, avoid if not urgent
- Market closed = queue for open (unless overnight risk is acceptable)
- RSI > 70 = Overbought, be cautious with BUYs (consider DELAY)
- RSI < 30 = Oversold, potential bounce (good for BUYs)
- MACD Hist < 0 = Bearish momentum (be cautious with BUYs)
- MACD Hist > 0 = Bullish momentum

EXAMPLES:
Example 1 - Execute Now:
TIMING: IMMEDIATE
SLIPPAGE: 0.05%
CONFIDENCE: 0.92
RECOMMENDATION: EXECUTE
(Good liquidity, tight spread, mid-day execution)

Example 2 - Wait for Open:
TIMING: WAIT_OPEN
SLIPPAGE: 0.15%
CONFIDENCE: 0.75
RECOMMENDATION: DELAY
(Market closed, queue order for 9:35 AM to avoid opening volatility)

Example 3 - Cancel:
TIMING: N/A
SLIPPAGE: N/A
CONFIDENCE: 0.30
RECOMMENDATION: CANCEL
(Spread 0.8% too wide, volume dried up, wait for better conditions)

NOW DECIDE FOR {symbol} {action}:
TIMING: [IMMEDIATE/WAIT_5MIN/WAIT_OPEN]
SLIPPAGE: [expected %]
CONFIDENCE: [0-1]
RECOMMENDATION: [EXECUTE/DELAY/CANCEL]"""

        # Get LLM analysis
        response = self.reason_with_llm(prompt)

        # Parse response
        analysis = self._parse_execution_response(response["reasoning"])
        analysis["market_status"] = market_status
        analysis["full_reasoning"] = response["reasoning"]
        analysis["trace_id"] = trace_id

        # Emit Decision Event
        self.audit_graph.emit(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                trace_id=trace_id,
                event_type=EventType.DECISION,
                agent_id=self.name,
                data=analysis,
            )
        )

        # Deterministic Constraint Check
        current_positions = 0
        trades_today = 0
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")

        if self.alpaca_api:
            try:
                current_positions = len(self.alpaca_api.get_all_positions())
            except Exception: # nosec
                pass

        # Count trades taken today (from ledger)
        try:
            with open("data/trades.json") as f:
                history = json.load(f).get("trades", [])
                trades_today = len([t for t in history if t.get("entry_date") == today_str])
        except Exception: # nosec
            pass

        # Extract metrics for Win Rate Optimization (P0)
        vix_val = 0.0
        try:
            vix_hist = self.data_provider.get_daily_bars("^VIX", lookback_days=1)
            if not vix_hist.data.empty:
                vix_val = vix_hist.data["Close"].iloc[-1]
        except Exception: # nosec
            pass

        # For multi-leg, calculate width
        width_val = 100.0
        if "legs" in data:
            # Simple width heuristic for ICs: distance between put strikes
            try:
                # Expecting data['legs'] to be list of OCC symbols or strike floats
                # (Simplified for now - will be expanded as needed)
                pass
            except Exception:
                pass

        constraint_result = self.constraint_engine.validate_trade(
            symbol,
            position_size,
            current_positions,
            trades_today=trades_today,
            metadata={
                "vix": vix_val,
                "width": width_val,
                "weekday": datetime.datetime.now().weekday(),
            },
        )

        # Emit Validation Event
        self.audit_graph.emit(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                trace_id=trace_id,
                event_type=EventType.VALIDATION,
                agent_id=self.name,
                data=constraint_result.__dict__,
            )
        )

        if not constraint_result.passed:
            logger.warning(f"Trade blocked by constraints: {constraint_result.violations}")
            analysis["action"] = "CANCEL"
            analysis["reasoning"] = f"BLOCKED: {constraint_result.violations}"

        # Execute if recommended and passed constraints
        if analysis["action"] == "EXECUTE" and self.alpaca_api:
            execution_result = self._execute_order(symbol, action, position_size)
            analysis["execution_result"] = execution_result

            # Emit Execution Event
            self.audit_graph.emit(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    trace_id=trace_id,
                    event_type=EventType.EXECUTION,
                    agent_id=self.name,
                    data=execution_result,
                )
            )
        else:
            analysis["execution_result"] = {
                "status": "NOT_EXECUTED",
                "reason": analysis["action"],
            }

        # Log decision
        self.log_decision(analysis)

        return analysis
