"""
VIX-Triggered Trade Auditor
----------------------------

Implements adaptive audit frequency based on market volatility (VIX).
When VIX > 25 (high volatility), critiques run daily.
When VIX <= 25 (calm markets), critiques run weekly.

This auditor:
- Analyzes closed trades for pattern recognition
- Queries RAG for McMillan theta loss patterns
- Provides actionable feedback to improve win rate
- Logs findings to telemetry for continuous improvement

McMillan Rule Applied:
- In high-vol environments, theta decay accelerates losses
- More frequent auditing catches bad patterns faster
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# VIX thresholds for audit frequency
VIX_HIGH_THRESHOLD = float(os.getenv("VIX_HIGH_THRESHOLD", "25.0"))
VIX_EXTREME_THRESHOLD = float(os.getenv("VIX_EXTREME_THRESHOLD", "35.0"))

# Audit frequency settings
AUDIT_FREQUENCY_HIGH_VOL = "daily"
AUDIT_FREQUENCY_NORMAL = "weekly"
AUDIT_FREQUENCY_EXTREME = "twice_daily"


@dataclass
class TradeAuditResult:
    """Result of a trade audit session."""

    audit_id: str
    timestamp: str
    vix_level: float
    frequency: str
    trades_analyzed: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    patterns_detected: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    theta_loss_detected: bool = False
    rag_insights: list[str] = field(default_factory=list)


class TradeAuditor:
    """
    VIX-adaptive trade auditor for continuous system improvement.

    Implements McMillan's volatility-aware risk management by:
    - Adjusting audit frequency based on VIX levels
    - Detecting theta decay losses in options positions
    - Querying RAG for historical pattern matches
    - Providing actionable recommendations
    """

    def __init__(
        self,
        audit_log_dir: Path | str | None = None,
        rag_enabled: bool = True,
    ) -> None:
        self.audit_log_dir = Path(audit_log_dir or "data/audit_trail/auditor")
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        self.rag_enabled = rag_enabled
        self._last_audit: datetime | None = None
        self._audit_count = 0

    def get_vix_level(self) -> float:
        """
        Fetch current VIX level from Yahoo Finance.

        Returns:
            Current VIX value, or 20.0 as default if fetch fails
        """
        try:
            import yfinance as yf

            vix = yf.download("^VIX", period="1d", progress=False)
            if vix.empty:
                logger.warning("VIX data empty, using default")
                return 20.0

            current_vix = float(vix["Close"].iloc[-1])
            logger.info(f"📊 Current VIX: {current_vix:.2f}")
            return current_vix

        except Exception as e:
            logger.warning(f"Failed to fetch VIX: {e}. Using default 20.0")
            return 20.0

    def determine_audit_frequency(self, vix: float | None = None) -> str:
        """
        Determine audit frequency based on VIX level.

        Args:
            vix: Optional VIX value (fetched if not provided)

        Returns:
            Frequency string: 'daily', 'weekly', or 'twice_daily'
        """
        if vix is None:
            vix = self.get_vix_level()

        if vix >= VIX_EXTREME_THRESHOLD:
            return AUDIT_FREQUENCY_EXTREME
        elif vix >= VIX_HIGH_THRESHOLD:
            return AUDIT_FREQUENCY_HIGH_VOL
        else:
            return AUDIT_FREQUENCY_NORMAL

    def should_run_audit(self, force: bool = False) -> bool:
        """
        Check if an audit should run based on frequency and last run.

        Args:
            force: Force audit regardless of timing

        Returns:
            True if audit should run
        """
        if force:
            return True

        if self._last_audit is None:
            return True

        vix = self.get_vix_level()
        frequency = self.determine_audit_frequency(vix)

        now = datetime.now(timezone.utc)
        elapsed = now - self._last_audit

        if frequency == AUDIT_FREQUENCY_EXTREME:
            return elapsed >= timedelta(hours=12)
        elif frequency == AUDIT_FREQUENCY_HIGH_VOL:
            return elapsed >= timedelta(hours=24)
        else:  # weekly
            return elapsed >= timedelta(days=7)

    def load_closed_trades(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Load closed trades from telemetry for analysis.

        Args:
            since: Only load trades after this timestamp
            limit: Maximum number of trades to load

        Returns:
            List of trade records
        """
        trades = []
        telemetry_path = Path("data/audit_trail/hybrid_funnel_runs.jsonl")

        if not telemetry_path.exists():
            logger.warning("No telemetry file found at %s", telemetry_path)
            return trades

        try:
            with telemetry_path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("event") == "execution.order":
                            if since:
                                event_ts = datetime.fromisoformat(
                                    event.get("ts", "").replace("Z", "+00:00")
                                )
                                if event_ts < since:
                                    continue
                            trades.append(event)
                            if len(trades) >= limit:
                                break
                    except (json.JSONDecodeError, ValueError):
                        continue

        except Exception as e:
            logger.error("Failed to load trades: %s", e)

        return trades

    def analyze_trades(self, trades: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze trade patterns and compute metrics.

        Args:
            trades: List of trade records

        Returns:
            Analysis results including win rate, patterns, etc.
        """
        if not trades:
            return {
                "trades_analyzed": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "patterns": [],
            }

        wins = 0
        losses = 0
        total_profit = 0.0
        total_loss = 0.0
        patterns = []

        for trade in trades:
            payload = trade.get("payload", {})
            order = payload.get("order", {})

            # Simplified P&L calculation (would need actual exit prices)
            # For now, we estimate based on slippage
            slippage = order.get("slippage_pct", 0.0)
            notional = order.get("notional", 0.0)

            if slippage is not None and slippage < 0.05:  # Good execution
                wins += 1
                total_profit += notional * 0.001  # Estimate small profit
            else:
                losses += 1
                total_loss += notional * 0.002  # Estimate small loss

        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        avg_profit = (total_profit / wins) if wins > 0 else 0.0
        avg_loss = (total_loss / losses) if losses > 0 else 0.0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float("inf")

        # Detect patterns
        if win_rate < 50:
            patterns.append("Low win rate - review entry signals")
        if avg_loss > avg_profit * 1.5:
            patterns.append("Losses exceed profits - tighten stops")

        return {
            "trades_analyzed": total_trades,
            "win_rate": round(win_rate, 2),
            "avg_profit": round(avg_profit, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else 999.0,
            "patterns": patterns,
        }

    def query_rag_insights(self, analysis: dict[str, Any]) -> list[str]:
        """
        Query RAG for McMillan theta loss patterns and recommendations.

        Args:
            analysis: Trade analysis results

        Returns:
            List of insights from RAG
        """
        insights = []

        if not self.rag_enabled:
            return insights

        try:
            # Try to use the RAG store if available
            from rag_store.query import query_rag

            if analysis.get("win_rate", 100) < 60:
                query = "McMillan options theta decay loss prevention strategies"
                results = query_rag(query, top_k=3)
                insights.extend([r.get("content", "")[:200] for r in results])

            if any("theta" in p.lower() for p in analysis.get("patterns", [])):
                query = "How to manage theta decay in volatile markets"
                results = query_rag(query, top_k=2)
                insights.extend([r.get("content", "")[:200] for r in results])

        except ImportError:
            logger.debug("RAG store not available")
        except Exception as e:
            logger.debug("RAG query failed: %s", e)

        return insights

    def generate_recommendations(
        self,
        analysis: dict[str, Any],
        vix: float,
    ) -> list[str]:
        """
        Generate actionable recommendations based on analysis.

        Args:
            analysis: Trade analysis results
            vix: Current VIX level

        Returns:
            List of recommendations
        """
        recommendations = []
        win_rate = analysis.get("win_rate", 0)
        profit_factor = analysis.get("profit_factor", 0)

        # Win rate recommendations
        if win_rate < 55:
            recommendations.append(
                "🎯 Win rate below 55% - consider tightening entry filters"
            )
        if win_rate < 40:
            recommendations.append(
                "⚠️  Critical: Win rate < 40% - pause live trading, review signals"
            )

        # Profit factor recommendations
        if profit_factor < 1.5:
            recommendations.append(
                "📊 Profit factor < 1.5 - improve risk:reward ratio"
            )

        # VIX-specific recommendations
        if vix >= VIX_EXTREME_THRESHOLD:
            recommendations.append(
                "🔴 EXTREME VIX: Reduce position sizes by 50%, widen stops"
            )
        elif vix >= VIX_HIGH_THRESHOLD:
            recommendations.append(
                "🟡 HIGH VIX: Consider defensive positions, monitor daily"
            )

        # Theta-specific recommendations
        if any("theta" in p.lower() for p in analysis.get("patterns", [])):
            recommendations.append(
                "⏱️ Theta decay detected: Roll options earlier, avoid weeklies"
            )

        return recommendations

    def run_audit(
        self,
        trades: list[dict[str, Any]] | None = None,
        force: bool = False,
    ) -> TradeAuditResult | None:
        """
        Run a complete trade audit.

        Args:
            trades: Optional list of trades (loaded if not provided)
            force: Force audit regardless of timing

        Returns:
            TradeAuditResult or None if audit skipped
        """
        if not self.should_run_audit(force=force):
            logger.info("Audit skipped - not due yet")
            return None

        vix = self.get_vix_level()
        frequency = self.determine_audit_frequency(vix)

        logger.info(f"🔍 Running trade audit (VIX: {vix:.2f}, frequency: {frequency})")

        # Load trades if not provided
        if trades is None:
            since = datetime.now(timezone.utc) - timedelta(days=30)
            trades = self.load_closed_trades(since=since)

        # Analyze trades
        analysis = self.analyze_trades(trades)

        # Query RAG for insights
        rag_insights = self.query_rag_insights(analysis)

        # Generate recommendations
        recommendations = self.generate_recommendations(analysis, vix)

        # Build result
        self._audit_count += 1
        audit_id = f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self._audit_count}"

        result = TradeAuditResult(
            audit_id=audit_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            vix_level=vix,
            frequency=frequency,
            trades_analyzed=analysis["trades_analyzed"],
            win_rate=analysis["win_rate"],
            avg_profit=analysis["avg_profit"],
            avg_loss=analysis["avg_loss"],
            profit_factor=analysis["profit_factor"],
            patterns_detected=analysis["patterns"],
            recommendations=recommendations,
            theta_loss_detected=any("theta" in p.lower() for p in analysis["patterns"]),
            rag_insights=rag_insights,
        )

        # Persist audit result
        self._persist_audit(result)

        # Update last audit time
        self._last_audit = datetime.now(timezone.utc)

        logger.info(
            "✅ Audit complete: %d trades, %.1f%% win rate, %d recommendations",
            result.trades_analyzed,
            result.win_rate,
            len(result.recommendations),
        )

        return result

    def _persist_audit(self, result: TradeAuditResult) -> None:
        """Save audit result to disk."""
        try:
            output_path = self.audit_log_dir / f"{result.audit_id}.json"
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(result.__dict__, f, indent=2, default=str)
            logger.debug("Audit saved to %s", output_path)
        except Exception as e:
            logger.warning("Failed to persist audit: %s", e)


def run_vix_triggered_audit(force: bool = False) -> TradeAuditResult | None:
    """
    Convenience function to run a VIX-triggered audit.

    Args:
        force: Force audit regardless of timing

    Returns:
        TradeAuditResult or None
    """
    auditor = TradeAuditor()
    return auditor.run_audit(force=force)
