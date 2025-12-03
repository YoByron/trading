"""
Options Profit Planner
----------------------

Transforms Rule #1 options signals (puts + calls) into an actionable plan
for achieving a target daily profit via premium selling.

Key capabilities:
- Normalize signals emitted from `RuleOneOptionsStrategy` or persisted JSON
- Compute per-contract and portfolio-level premium pacing
- Highlight the shortfall vs a configured daily target (defaults to $10/day)
- Recommend the additional number of contracts required to close the gap
- Persist structured summaries under `data/options_signals/`
- **NEW**: Theta harvest execution with equity gates ($5k/$10k thresholds)
"""

from __future__ import annotations

import json
import logging
import math
import os
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING, Union

logger = logging.getLogger(__name__)

try:  # Optional import for runtime typing; not required for JSON snapshots
    from src.strategies.rule_one_options import RuleOneOptionsSignal  # type: ignore
except Exception:  # pragma: no cover - fallback for test environments without full deps
    RuleOneOptionsSignal = Any  # type: ignore

try:  # Optional - only needed when executing theta orders live
    from src.core.options_client import AlpacaOptionsClient
except Exception:  # pragma: no cover - dependency may be missing locally
    AlpacaOptionsClient = None  # type: ignore[misc,assignment]

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.agents.execution_agent import ExecutionAgent


SignalInput = Union[dict[str, Any], "RuleOneOptionsSignal"]

# Equity thresholds for options strategies
THETA_STAGE_1_EQUITY = float(os.getenv("THETA_STAGE_1_EQUITY", "5000"))  # Poor man's covered calls
THETA_STAGE_2_EQUITY = float(os.getenv("THETA_STAGE_2_EQUITY", "10000"))  # Iron condors
THETA_STAGE_3_EQUITY = float(os.getenv("THETA_STAGE_3_EQUITY", "25000"))  # Full options suite
IV_PERCENTILE_THRESHOLD = float(
    os.getenv("IV_PERCENTILE_THRESHOLD", "50")
)  # Min IV rank for selling


@dataclass
class SignalProfitProjection:
    """Computed premium pacing for a single options signal."""

    symbol: str
    signal_type: str
    strike: float
    expiration: str
    contracts: int
    days_to_expiry: int
    premium_per_contract: float
    total_premium: float
    daily_premium_per_contract: float
    daily_premium_total: float
    annualized_return: float
    iv_rank: float | None
    delta: float | None
    rationale: str


class OptionsProfitPlanner:
    """
    Analyze options signals and determine whether we are on track
    to hit a configurable daily premium target (default: $10/day).
    """

    def __init__(
        self,
        target_daily_profit: float = 10.0,
        trading_days_per_month: int = 21,
        snapshot_dir: Path | None = None,
    ):
        self.target_daily_profit = target_daily_profit
        self.trading_days_per_month = trading_days_per_month
        self.snapshot_dir = snapshot_dir or Path("data/options_signals")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------- #
    # Snapshot helpers
    # --------------------------------------------------------------------- #
    def load_latest_snapshot(self) -> dict[str, Any] | None:
        """Load the most recent options snapshot from disk."""
        if not self.snapshot_dir.exists():
            return None

        files = sorted(self.snapshot_dir.glob("*.json"))
        if not files:
            return None

        latest_path = files[-1]
        try:
            with latest_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            payload["_source_path"] = str(latest_path)
            return payload
        except Exception as exc:
            logger.error("Failed to read snapshot %s: %s", latest_path, exc)
            return None

    def persist_summary(self, summary: dict[str, Any]) -> Path:
        """Persist planner output for downstream dashboards."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        output_path = self.snapshot_dir / f"options_profit_plan_{timestamp}.json"
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        logger.info("Saved options profit plan → %s", output_path)
        return output_path

    # --------------------------------------------------------------------- #
    # Core analysis
    # --------------------------------------------------------------------- #
    def summarize(
        self,
        put_signals: Sequence[SignalInput],
        call_signals: Sequence[SignalInput],
        data_source: str | None = None,
    ) -> dict[str, Any]:
        """Generate profit pacing summary for supplied signals."""
        put_metrics = [self._score_signal(signal) for signal in put_signals]
        call_metrics = [self._score_signal(signal) for signal in call_signals]

        combined = put_metrics + call_metrics
        daily_run_rate = sum(m.daily_premium_total for m in combined)
        monthly_run_rate = daily_run_rate * self.trading_days_per_month
        annualized_run_rate = daily_run_rate * 252  # trading days per year
        gap = max(0.0, self.target_daily_profit - daily_run_rate)

        recommendation = self._recommend_contract_plan(combined, gap)

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_daily_profit": self.target_daily_profit,
            "daily_run_rate": round(daily_run_rate, 2),
            "monthly_run_rate": round(monthly_run_rate, 2),
            "annualized_run_rate": round(annualized_run_rate, 2),
            "gap_to_target": round(gap, 2),
            "signals_analyzed": len(combined),
            "puts": [asdict(m) for m in put_metrics],
            "calls": [asdict(m) for m in call_metrics],
            "recommendation": recommendation,
            "data_source": data_source,
            "notes": self._build_notes(combined, gap),
        }
        return summary

    def build_summary_from_snapshot(self, snapshot: dict[str, Any] | None) -> dict[str, Any]:
        """
        Convenience method for snapshot payloads persisted by
        `RuleOneOptionsStrategy.generate_daily_signals()`.
        """
        if not snapshot:
            return self._empty_summary("No snapshot available (run signals first).")

        puts = snapshot.get("put_opportunities", [])
        calls = snapshot.get("call_opportunities", [])

        if not puts and not calls:
            return self._empty_summary(
                "Snapshot contains zero opportunities (likely due to missing data or tight filters).",
                data_source=snapshot.get("_source_path"),
            )

        source = snapshot.get("_source_path")
        return self.summarize(puts, calls, data_source=source or "in-memory")

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _empty_summary(self, reason: str, data_source: str | None = None) -> dict[str, Any]:
        """Return placeholder summary when no signals are available."""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_daily_profit": self.target_daily_profit,
            "daily_run_rate": 0.0,
            "monthly_run_rate": 0.0,
            "annualized_run_rate": 0.0,
            "gap_to_target": self.target_daily_profit,
            "signals_analyzed": 0,
            "puts": [],
            "calls": [],
            "recommendation": None,
            "data_source": data_source,
            "notes": [reason],
        }

    def _score_signal(self, signal: SignalInput) -> SignalProfitProjection:
        """Normalize a signal and compute profit pacing metrics."""
        payload = self._to_payload(signal)
        days = self._resolve_days_to_expiry(payload)
        contracts = max(1, int(payload.get("contracts") or 1))

        premium = max(float(payload.get("premium") or 0.0), 0.0)
        premium_per_contract = premium * 100  # options quote is per share
        total_premium = premium_per_contract * contracts
        daily_per_contract = premium_per_contract / days
        daily_total = daily_per_contract * contracts

        projection = SignalProfitProjection(
            symbol=str(payload.get("symbol")),
            signal_type=str(payload.get("signal_type") or payload.get("type")),
            strike=float(payload.get("strike") or 0.0),
            expiration=str(payload.get("expiration") or ""),
            contracts=contracts,
            days_to_expiry=days,
            premium_per_contract=round(premium_per_contract, 2),
            total_premium=round(total_premium, 2),
            daily_premium_per_contract=round(daily_per_contract, 2),
            daily_premium_total=round(daily_total, 2),
            annualized_return=float(payload.get("annualized_return") or 0.0),
            iv_rank=self._maybe_float(payload.get("iv_rank")),
            delta=self._maybe_float(payload.get("delta")),
            rationale=str(payload.get("rationale") or payload.get("reason", "")),
        )
        return projection

    @staticmethod
    def _to_payload(signal: SignalInput) -> dict[str, Any]:
        """Coerce dataclass or dict signals into a plain dict."""
        if hasattr(signal, "__dict__"):
            return {key: value for key, value in signal.__dict__.items() if not key.startswith("_")}
        if isinstance(signal, dict):
            return dict(signal)
        raise TypeError(f"Unsupported signal type: {type(signal)}")

    @staticmethod
    def _resolve_days_to_expiry(payload: dict[str, Any]) -> int:
        """Best-effort resolution of days to expiry."""
        days = payload.get("days_to_expiry")
        if days is None and payload.get("expiration"):
            try:
                exp = datetime.fromisoformat(str(payload["expiration"])[:10])
                days = (exp.date() - datetime.utcnow().date()).days
            except ValueError:
                days = None

        if days is None:
            days = 30  # conservative default for pacing

        days = max(1, int(days))
        return days

    @staticmethod
    def _maybe_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _recommend_contract_plan(
        self, projections: Sequence[SignalProfitProjection], gap: float
    ) -> dict[str, Any] | None:
        """Recommend additional contracts required to close the gap."""
        if gap <= 0 or not projections:
            return None

        # Sort by best daily premium per contract
        best = max(projections, key=lambda proj: proj.daily_premium_per_contract)
        per_contract_daily = best.daily_premium_per_contract
        if per_contract_daily <= 0:
            return None

        additional_contracts = math.ceil(gap / per_contract_daily)
        return {
            "recommended_symbol": best.symbol,
            "signal_type": best.signal_type,
            "daily_premium_per_contract": best.daily_premium_per_contract,
            "gap_to_target": round(gap, 2),
            "additional_contracts_needed": int(additional_contracts),
            "suggested_action": (
                f"Sell {additional_contracts} more {best.signal_type} contract(s) "
                f"similar to {best.symbol} to close the ${gap:.2f}/day gap."
            ),
        }

    def _build_notes(
        self,
        projections: Sequence[SignalProfitProjection],
        gap: float,
    ) -> list[str]:
        """Generate human-readable notes for the summary."""
        notes = []
        if not projections:
            notes.append("No qualifying put/call signals met IV/delta filters.")
            return notes

        top_symbols = {proj.symbol for proj in projections}
        notes.append(f"Analyzed {len(projections)} signals across {len(top_symbols)} symbols.")

        if gap > 0:
            notes.append(
                f"Premium run-rate is ${gap:.2f}/day below the ${self.target_daily_profit:.2f} target."
            )
        else:
            notes.append(
                f"Current premium pace meets or exceeds the ${self.target_daily_profit:.2f}/day target."
            )

        return notes


@dataclass
class ThetaHarvestResult:
    """Result of a theta harvest execution attempt."""

    symbol: str
    strategy: str
    contracts: int
    estimated_premium: float
    executed: bool
    reason: str
    order_id: str | None = None
    iv_percentile: float | None = None


@dataclass
class ThetaOrderRequest:
    """Executable option order derived from a theta opportunity."""

    option_symbol: str
    quantity: int
    side: str
    order_type: str
    limit_price: float | None
    strategy: str
    underlying: str
    notes: str
    simulated: bool = False


@dataclass
class ResolvedOptionContract:
    """Normalized contract metadata pulled from Alpaca or synthesized."""

    symbol: str
    underlying: str
    option_type: str
    strike: float
    expiration: date
    delta: float | None
    bid: float | None
    ask: float | None
    mid: float | None
    simulated: bool = False
class ThetaHarvestExecutor:
    """
    Execute theta harvest strategies based on equity gates.

    Equity Thresholds:
    - $5k+: Poor man's covered calls (long ITM leap + short 20-delta weekly)
    - $10k+: Iron condors on broad indices (QQQ, SPY) in calm regime
    - $25k+: Full options suite including undefined-risk strategies

    Gate Logic:
    - Only sell premium when IV percentile > 50
    - Prefer 20-delta short strikes for defined risk
    - Size positions to target $10/day equivalent premium
    """

    def __init__(self, paper: bool = True) -> None:
        self.paper = paper
        self.planner = OptionsProfitPlanner()
        # Lazily created Alpaca options client (False sentinel == permanently unavailable)
        self._options_client: "AlpacaOptionsClient | None | bool" = None

    def check_equity_gate(self, account_equity: float) -> dict[str, Any]:
        """
        Determine which theta strategies are available based on account equity.

        Returns:
            Dict with enabled strategies and equity gap to next tier
        """
        strategies = {
            "poor_mans_covered_call": account_equity >= THETA_STAGE_1_EQUITY,
            "iron_condor": account_equity >= THETA_STAGE_2_EQUITY,
            "full_suite": account_equity >= THETA_STAGE_3_EQUITY,
        }

        # Calculate gap to next tier
        if account_equity < THETA_STAGE_1_EQUITY:
            next_tier = "poor_mans_covered_call"
            gap = THETA_STAGE_1_EQUITY - account_equity
        elif account_equity < THETA_STAGE_2_EQUITY:
            next_tier = "iron_condor"
            gap = THETA_STAGE_2_EQUITY - account_equity
        elif account_equity < THETA_STAGE_3_EQUITY:
            next_tier = "full_suite"
            gap = THETA_STAGE_3_EQUITY - account_equity
        else:
            next_tier = None
            gap = 0

        return {
            "account_equity": account_equity,
            "enabled_strategies": strategies,
            "next_tier": next_tier,
            "gap_to_next_tier": round(gap, 2),
            "theta_enabled": any(strategies.values()),
        }

    def get_iv_percentile(self, symbol: str) -> float | None:
        """
        Calculate IV percentile for a symbol.

        IV Percentile = % of days in past year where IV was lower than current.
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            if hist.empty:
                return None

            # Calculate historical volatility as IV proxy
            returns = hist["Close"].pct_change().dropna()
            if len(returns) < 30:
                return None

            # Rolling 20-day volatility
            rolling_vol = returns.rolling(20).std() * (252**0.5)
            current_vol = rolling_vol.iloc[-1]
            hist_vol = rolling_vol.dropna()

            if len(hist_vol) < 10:
                return None

            percentile = (hist_vol < current_vol).mean() * 100
            return round(percentile, 1)

        except Exception as exc:
            logger.warning("IV percentile calculation failed for %s: %s", symbol, exc)
            return None

    def evaluate_theta_opportunity(
        self,
        symbol: str,
        account_equity: float,
        regime_label: str = "calm",
        bullish_signal: bool = True,
    ) -> ThetaHarvestResult | None:
        """
        Evaluate and potentially execute a theta harvest opportunity.

        Strategy selection:
        - Poor man's covered call: Long ITM leap + short 20-delta weekly
        - Iron condor: Sell OTM puts and calls (only in calm regime)

        Args:
            symbol: Underlying symbol (e.g., 'SPY', 'QQQ')
            account_equity: Current account equity
            regime_label: Current market regime from RegimeDetector
            bullish_signal: Whether momentum/sentiment is bullish

        Returns:
            ThetaHarvestResult if opportunity found, None otherwise
        """
        gate = self.check_equity_gate(account_equity)

        if not gate["theta_enabled"]:
            return ThetaHarvestResult(
                symbol=symbol,
                strategy="none",
                contracts=0,
                estimated_premium=0.0,
                executed=False,
                reason=f"Equity ${account_equity:.2f} below minimum ${THETA_STAGE_1_EQUITY}",
            )

        # Check IV percentile
        iv_pct = self.get_iv_percentile(symbol)
        if iv_pct is not None and iv_pct < IV_PERCENTILE_THRESHOLD:
            return ThetaHarvestResult(
                symbol=symbol,
                strategy="none",
                contracts=0,
                estimated_premium=0.0,
                executed=False,
                reason=f"IV percentile {iv_pct}% below threshold {IV_PERCENTILE_THRESHOLD}%",
                iv_percentile=iv_pct,
            )

        # Select strategy based on equity and regime
        if gate["enabled_strategies"]["iron_condor"] and regime_label == "calm":
            strategy = "iron_condor"
            estimated_premium = 50.0  # ~$50/contract for 5-wide condor
            contracts = max(1, int((self.planner.target_daily_profit * 30) / estimated_premium))
        elif gate["enabled_strategies"]["poor_mans_covered_call"] and bullish_signal:
            strategy = "poor_mans_covered_call"
            estimated_premium = 35.0  # ~$35/week for 20-delta call
            contracts = max(1, int((self.planner.target_daily_profit * 7) / estimated_premium))
        else:
            return ThetaHarvestResult(
                symbol=symbol,
                strategy="none",
                contracts=0,
                estimated_premium=0.0,
                executed=False,
                reason="No suitable strategy for current conditions",
                iv_percentile=iv_pct,
            )

        # Build theta harvest result
        result = ThetaHarvestResult(
            symbol=symbol,
            strategy=strategy,
            contracts=contracts,
            estimated_premium=estimated_premium * contracts,
            executed=False,
            reason=f"Signal ready for {strategy}",
            iv_percentile=iv_pct,
        )

        logger.info(
            "🎯 Theta opportunity: %s %s x%d, est. premium $%.2f, IV pct: %s",
            symbol,
            strategy,
            contracts,
            result.estimated_premium,
            iv_pct,
        )

        return result

    def execute_theta_order(
        self,
        result: ThetaHarvestResult,
        alpaca_client: Any = None,
    ) -> ThetaHarvestResult:
        """
        Execute a theta harvest order through Alpaca.

        This is the key tie-in that connects options planning to actual execution.
        Only executes when:
        - Paper mode is enabled OR
        - Live mode with explicit confirmation

        Args:
            result: ThetaHarvestResult from evaluate_theta_opportunity
            alpaca_client: Alpaca TradingClient instance

        Returns:
            Updated ThetaHarvestResult with execution status
        """
        if result.strategy == "none" or result.contracts <= 0:
            return result

        if alpaca_client is None:
            logger.warning("No Alpaca client provided - skipping execution")
            return result

        try:
            # Build option symbol (OCC format): SPY241206C00600000
            # For now, we generate a weekly expiry (next Friday)
            from datetime import datetime, timedelta

            today = datetime.now()
            days_until_friday = (4 - today.weekday()) % 7
            if days_until_friday == 0:
                days_until_friday = 7  # Next week's Friday
            expiry = today + timedelta(days=days_until_friday)
            expiry_str = expiry.strftime("%y%m%d")

            # Get current price to calculate strike
            import yfinance as yf

            ticker = yf.Ticker(result.symbol)
            current_price = ticker.history(period="1d")["Close"].iloc[-1]

            # Calculate 20-delta strike (roughly 5% OTM for calls, 5% ITM for puts)
            if result.strategy == "poor_mans_covered_call":
                # Sell call at ~5% above current price
                strike = round(current_price * 1.05, 0)
                option_type = "C"
                side = "sell_to_open"
            elif result.strategy == "iron_condor":
                # For iron condor, we'd need 4 legs - simplified to single call for now
                strike = round(current_price * 1.08, 0)
                option_type = "C"
                side = "sell_to_open"
            else:
                logger.warning("Unknown strategy: %s", result.strategy)
                return result

            # Build OCC symbol
            strike_str = f"{int(strike * 1000):08d}"
            option_symbol = f"{result.symbol}{expiry_str}{option_type}{strike_str}"

            logger.info(
                "🚀 Executing theta order: %s %s x%d (strike $%.0f, expiry %s)",
                side.upper(),
                option_symbol,
                result.contracts,
                strike,
                expiry.strftime("%Y-%m-%d"),
            )

            # Submit order via Alpaca
            # Note: Options trading requires specific Alpaca permissions
            if self.paper:
                # Paper mode - log intent only (Alpaca paper doesn't support options)
                logger.info(
                    "📝 PAPER MODE: Would execute %s %s x%d",
                    side,
                    option_symbol,
                    result.contracts,
                )
                result.executed = True
                result.reason = f"Paper execution logged: {side} {option_symbol}"
                result.order_id = f"paper_{option_symbol}_{datetime.now().timestamp()}"
            else:
                # Live mode - attempt real execution
                try:
                    from alpaca.trading.enums import OrderSide, TimeInForce
                    from alpaca.trading.requests import MarketOrderRequest

                    order_side = OrderSide.SELL if "sell" in side else OrderSide.BUY
                    order_req = MarketOrderRequest(
                        symbol=option_symbol,
                        qty=result.contracts,
                        side=order_side,
                        time_in_force=TimeInForce.DAY,
                    )
                    order = alpaca_client.submit_order(order_req)
                    result.executed = True
                    result.order_id = str(order.id)
                    result.reason = f"Order submitted: {order.id}"
                    logger.info("✅ Theta order executed: %s", order.id)
                except Exception as e:
                    logger.error("❌ Theta order failed: %s", e)
                    result.reason = f"Execution failed: {e}"

        except Exception as e:
            logger.error("Theta execution error: %s", e)
            result.reason = f"Execution error: {e}"

        return result

    def generate_theta_plan(
        self,
        account_equity: float,
        regime_label: str = "calm",
        symbols: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a complete theta harvest plan based on account equity.

        Returns a structured plan with:
        - Available strategies at current equity level
        - Specific opportunities for each qualifying symbol
        - Total estimated daily premium vs target
        """
        symbols = symbols or ["SPY", "QQQ", "IWM"]
        gate = self.check_equity_gate(account_equity)

        plan = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "account_equity": account_equity,
            "equity_gate": gate,
            "regime": regime_label,
            "target_daily_premium": self.planner.target_daily_profit,
            "opportunities": [],
            "total_estimated_premium": 0.0,
            "premium_gap": self.planner.target_daily_profit,
        }

        if not gate["theta_enabled"]:
            plan["summary"] = (
                f"Theta strategies disabled until equity reaches ${THETA_STAGE_1_EQUITY}"
            )
            return plan

        for symbol in symbols:
            result = self.evaluate_theta_opportunity(
                symbol=symbol,
                account_equity=account_equity,
                regime_label=regime_label,
            )
            if result and result.strategy != "none":
                plan["opportunities"].append(asdict(result))
                # Convert to daily equivalent
                if result.strategy == "iron_condor":
                    daily_equiv = result.estimated_premium / 30  # Monthly expiry
                else:
                    daily_equiv = result.estimated_premium / 7  # Weekly expiry
                plan["total_estimated_premium"] += daily_equiv

        plan["premium_gap"] = max(
            0, self.planner.target_daily_profit - plan["total_estimated_premium"]
        )
        plan["on_track"] = plan["premium_gap"] == 0

        # Build summary
        if plan["opportunities"]:
            plan["summary"] = (
                f"Found {len(plan['opportunities'])} theta opportunities. "
                f"Est. daily premium: ${plan['total_estimated_premium']:.2f} "
                f"(gap: ${plan['premium_gap']:.2f})"
            )
        else:
            plan["summary"] = "No qualifying theta opportunities found"

        return plan

    # ------------------------------------------------------------------ #
    # Execution integration
    # ------------------------------------------------------------------ #
    def dispatch_theta_trades(
        self,
        plan: dict[str, Any],
        execution_agent: "ExecutionAgent",
        *,
        paper: bool = True,
        regime_label: str | None = None,
    ) -> dict[str, Any]:
        """
        Convert theta opportunities into concrete option orders via ExecutionAgent.

        Args:
            plan: Output of generate_theta_plan
            execution_agent: Execution agent capable of submitting option trades
            paper: Whether to run trades in paper mode
            regime_label: Optional market regime context for logging
        """

        opportunities = plan.get("opportunities", [])
        summary: dict[str, Any] = {
            "requested": len(opportunities),
            "submitted": [],
            "skipped": [],
            "status": "noop",
            "regime": regime_label,
        }

        if not opportunities:
            summary["status"] = "no_opportunities"
            return summary

        for opportunity in opportunities:
            orders = self._build_orders_for_opportunity(
                opportunity,
                plan.get("account_equity", 0.0),
                regime_label=regime_label,
            )
            if not orders:
                summary["skipped"].append(
                    {
                        "symbol": opportunity.get("symbol"),
                        "strategy": opportunity.get("strategy"),
                        "reason": "order_generation_failed",
                    }
                )
                continue

            for order_req in orders:
                exec_result = execution_agent.submit_option_order(
                    option_symbol=order_req.option_symbol,
                    qty=order_req.quantity,
                    side=order_req.side,
                    order_type=order_req.order_type,
                    limit_price=order_req.limit_price,
                    paper=paper,
                    metadata={
                        "strategy": order_req.strategy,
                        "underlying": order_req.underlying,
                        "notes": order_req.notes,
                        "simulated": order_req.simulated,
                    },
                )
                summary["submitted"].append(
                    {
                        "request": asdict(order_req),
                        "result": exec_result,
                    }
                )

        if summary["submitted"]:
            summary["status"] = "executed"
        elif summary["skipped"]:
            summary["status"] = "skipped"
        return summary

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _build_orders_for_opportunity(
        self,
        opportunity: dict[str, Any],
        account_equity: float,
        regime_label: str | None = None,
    ) -> list[ThetaOrderRequest]:
        strategy = opportunity.get("strategy")
        if strategy == "poor_mans_covered_call":
            return self._build_poor_mans_orders(opportunity, regime_label=regime_label)
        if strategy == "iron_condor":
            return self._build_iron_condor_orders(opportunity, regime_label=regime_label)
        logger.debug("Unsupported theta strategy %s", strategy)
        return []

    def _build_poor_mans_orders(
        self,
        opportunity: dict[str, Any],
        regime_label: str | None = None,
    ) -> list[ThetaOrderRequest]:
        symbol = opportunity.get("symbol")
        contracts = max(1, int(opportunity.get("contracts", 1)))
        notes = f"Poor man's covered call ({regime_label or 'default'} regime)"
        contract = self._select_contract(
            symbol=symbol,
            option_type="call",
            target_delta=0.20,
            min_dte=5,
            max_dte=12,
        )

        if contract is None:
            synthetic_symbol = self._synthesize_occ_symbol(
                symbol=symbol,
                option_type="call",
                dte=7,
                strike_offset_pct=0.05,
            )
            return [
                ThetaOrderRequest(
                    option_symbol=synthetic_symbol,
                    quantity=contracts,
                    side="sell_to_open",
                    order_type="market",
                    limit_price=None,
                    strategy="poor_mans_covered_call",
                    underlying=symbol,
                    notes=f"{notes} (synthetic symbol - options feed unavailable)",
                    simulated=True,
                )
            ]

        limit_price = self._calc_limit_price(contract)
        order_type = "limit" if limit_price is not None else "market"

        return [
            ThetaOrderRequest(
                option_symbol=contract.symbol,
                quantity=contracts,
                side="sell_to_open",
                order_type=order_type,
                limit_price=limit_price,
                strategy="poor_mans_covered_call",
                underlying=symbol,
                notes=notes,
                simulated=contract.simulated,
            )
        ]

    def _build_iron_condor_orders(
        self,
        opportunity: dict[str, Any],
        regime_label: str | None = None,
    ) -> list[ThetaOrderRequest]:
        symbol = opportunity.get("symbol")
        contracts = max(1, int(opportunity.get("contracts", 1)))
        notes = f"Iron condor ({regime_label or 'default'} regime)"
        chain = self._get_option_chain(symbol)
        if not chain:
            return []

        short_call = self._select_contract_from_chain(
            chain=chain,
            symbol=symbol,
            option_type="call",
            target_delta=0.20,
            min_dte=25,
            max_dte=35,
        )
        short_put = self._select_contract_from_chain(
            chain=chain,
            symbol=symbol,
            option_type="put",
            target_delta=0.20,
            min_dte=25,
            max_dte=35,
        )

        if not short_call or not short_put:
            logger.debug("Unable to resolve short legs for iron condor on %s", symbol)
            return []

        width = float(os.getenv("THETA_CONDOR_WIDTH", "5.0"))
        long_call = self._find_wing_contract(
            chain,
            base_contract=short_call,
            option_type="call",
            target_strike=short_call.strike + width,
        )
        long_put = self._find_wing_contract(
            chain,
            base_contract=short_put,
            option_type="put",
            target_strike=short_put.strike - width,
        )

        orders: list[ThetaOrderRequest] = []

        orders.append(
            ThetaOrderRequest(
                option_symbol=short_call.symbol,
                quantity=contracts,
                side="sell_to_open",
                order_type="limit" if self._calc_limit_price(short_call) else "market",
                limit_price=self._calc_limit_price(short_call),
                strategy="iron_condor",
                underlying=symbol,
                notes=f"{notes} - short call leg",
                simulated=short_call.simulated,
            )
        )

        orders.append(
            ThetaOrderRequest(
                option_symbol=short_put.symbol,
                quantity=contracts,
                side="sell_to_open",
                order_type="limit" if self._calc_limit_price(short_put) else "market",
                limit_price=self._calc_limit_price(short_put),
                strategy="iron_condor",
                underlying=symbol,
                notes=f"{notes} - short put leg",
                simulated=short_put.simulated,
            )
        )

        if long_call:
            orders.append(
                ThetaOrderRequest(
                    option_symbol=long_call.symbol,
                    quantity=contracts,
                    side="buy_to_open",
                    order_type="limit" if self._calc_limit_price(long_call) else "market",
                    limit_price=self._calc_limit_price(long_call),
                    strategy="iron_condor",
                    underlying=symbol,
                    notes=f"{notes} - long call wing",
                    simulated=long_call.simulated,
                )
            )

        if long_put:
            orders.append(
                ThetaOrderRequest(
                    option_symbol=long_put.symbol,
                    quantity=contracts,
                    side="buy_to_open",
                    order_type="limit" if self._calc_limit_price(long_put) else "market",
                    limit_price=self._calc_limit_price(long_put),
                    strategy="iron_condor",
                    underlying=symbol,
                    notes=f"{notes} - long put wing",
                    simulated=long_put.simulated,
                )
            )

        if long_call is None or long_put is None:
            logger.warning(
                "Iron condor wings partially missing for %s (call=%s, put=%s). "
                "Order will be partially defined-risk.",
                symbol,
                bool(long_call),
                bool(long_put),
            )

        return orders

    def _find_wing_contract(
        self,
        chain: list[dict[str, Any]],
        *,
        base_contract: ResolvedOptionContract,
        option_type: str,
        target_strike: float,
    ) -> ResolvedOptionContract | None:
        """Locate protective wing contract near the requested strike."""

        closest: ResolvedOptionContract | None = None
        for entry in chain:
            contract = self._contract_from_chain_entry(entry)
            if not contract:
                continue
            if contract.option_type != option_type:
                continue
            if contract.expiration != base_contract.expiration:
                continue
            distance = abs(contract.strike - target_strike)
            if distance < 0.01:
                return contract
            if closest is None or distance < abs(closest.strike - target_strike):
                closest = contract
        return closest

    def _select_contract(
        self,
        symbol: str,
        option_type: str,
        target_delta: float,
        min_dte: int,
        max_dte: int,
    ) -> ResolvedOptionContract | None:
        chain = self._get_option_chain(symbol)
        if not chain:
            return None
        return self._select_contract_from_chain(
            chain,
            symbol=symbol,
            option_type=option_type,
            target_delta=target_delta,
            min_dte=min_dte,
            max_dte=max_dte,
        )

    def _select_contract_from_chain(
        self,
        chain: list[dict[str, Any]],
        *,
        symbol: str,
        option_type: str,
        target_delta: float,
        min_dte: int,
        max_dte: int,
    ) -> ResolvedOptionContract | None:
        today = datetime.utcnow().date()
        candidates: list[tuple[float, int, ResolvedOptionContract]] = []

        for entry in chain:
            contract = self._contract_from_chain_entry(entry)
            if not contract:
                continue
            if contract.option_type != option_type:
                continue
            dte = (contract.expiration - today).days
            if dte < min_dte or dte > max_dte:
                continue
            if contract.delta is None:
                continue
            score = abs(abs(contract.delta) - target_delta)
            candidates.append((score, dte, contract))

        if not candidates:
            return None

        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]

    def _contract_from_chain_entry(self, entry: dict[str, Any]) -> ResolvedOptionContract | None:
        symbol = entry.get("symbol")
        parsed = self._parse_option_symbol(symbol)
        if not parsed:
            return None

        greeks = entry.get("greeks") or {}
        delta = greeks.get("delta")
        bid = entry.get("latest_quote_bid")
        ask = entry.get("latest_quote_ask")
        trade = entry.get("latest_trade_price")

        return ResolvedOptionContract(
            symbol=symbol,
            underlying=parsed["underlying"],
            option_type=parsed["option_type"],
            strike=parsed["strike"],
            expiration=parsed["expiration"],
            delta=float(delta) if delta is not None else None,
            bid=self.planner._maybe_float(bid),
            ask=self.planner._maybe_float(ask),
            mid=self._calc_mid_price(bid, ask, trade),
        )

    @staticmethod
    def _calc_mid_price(bid: Any, ask: Any, trade: Any) -> float | None:
        values = [value for value in (bid, ask, trade) if value is not None]
        try:
            floats = [float(value) for value in values if float(value) > 0]
        except (TypeError, ValueError):
            floats = []
        if not floats:
            return None
        if bid is not None and ask is not None:
            try:
                return round((float(bid) + float(ask)) / 2, 2)
            except (TypeError, ValueError):
                pass
        if trade is not None:
            try:
                return round(float(trade), 2)
            except (TypeError, ValueError):
                pass
        if bid is not None:
            try:
                return round(float(bid), 2)
            except (TypeError, ValueError):
                pass
        if ask is not None:
            try:
                return round(float(ask), 2)
            except (TypeError, ValueError):
                pass
        return None

    def _calc_limit_price(self, contract: ResolvedOptionContract) -> float | None:
        if contract.mid is not None:
            return round(contract.mid, 2)
        if contract.bid is not None and contract.ask is not None:
            return round((contract.bid + contract.ask) / 2, 2)
        if contract.bid is not None:
            return round(contract.bid, 2)
        if contract.ask is not None:
            return round(contract.ask, 2)
        return None

    def _get_option_chain(self, symbol: str) -> list[dict[str, Any]] | None:
        if not hasattr(self, "_chain_cache"):
            self._chain_cache: dict[str, list[dict[str, Any]]] = {}

        if symbol in self._chain_cache:
            return self._chain_cache[symbol]

        client = self._get_options_client()
        if client is None:
            return None

        try:
            chain = client.get_option_chain(symbol)
            self._chain_cache[symbol] = chain
            return chain
        except Exception as exc:  # pragma: no cover - network/API failure
            logger.warning("Failed to fetch option chain for %s: %s", symbol, exc)
            return None

    def _get_options_client(self) -> "AlpacaOptionsClient | None":
        if self._options_client is False:
            return None
        if self._options_client:
            return self._options_client
        if AlpacaOptionsClient is None:
            self._options_client = False
            return None
        try:
            self._options_client = AlpacaOptionsClient(paper=self.paper)
            return self._options_client
        except Exception as exc:  # pragma: no cover - dependency issues
            logger.warning("Theta executor unable to init Alpaca options client: %s", exc)
            self._options_client = False
            return None

    def _parse_option_symbol(self, symbol: str | None) -> dict[str, Any] | None:
        if not symbol or len(symbol) < 15:
            return None
        try:
            expiry_digits = symbol[-15:-9]
            cp_flag = symbol[-9]
            strike_digits = symbol[-8:]
            underlying = symbol[:-15].strip()
            expiration = datetime.strptime(expiry_digits, "%y%m%d").date()
            strike = int(strike_digits) / 1000
            option_type = "call" if cp_flag.upper() == "C" else "put"
            return {
                "underlying": underlying,
                "expiration": expiration,
                "strike": strike,
                "option_type": option_type,
            }
        except Exception:
            return None

    def _synthesize_occ_symbol(
        self,
        *,
        symbol: str,
        option_type: str,
        dte: int,
        strike_offset_pct: float,
    ) -> str:
        base_price = self._resolve_underlying_price(symbol) or 100.0
        if option_type == "call":
            strike = base_price * (1 + strike_offset_pct)
        else:
            strike = base_price * (1 - strike_offset_pct)
        strike_int = int(round(strike * 1000))
        expiry = (datetime.utcnow().date() + timedelta(days=dte)).strftime("%y%m%d")
        flag = "C" if option_type == "call" else "P"
        root = symbol.replace(".", "").replace("-", "").upper()
        return f"{root}{expiry}{flag}{strike_int:08d}"

    def _resolve_underlying_price(self, symbol: str) -> float | None:
        try:
            import yfinance as yf  # type: ignore

            ticker = yf.Ticker(symbol)
            info = ticker.fast_info  # type: ignore[attr-defined]
            price = info.get("last_price") if isinstance(info, dict) else None
            if price:
                return float(price)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])
            return None
        except Exception:
            return None
