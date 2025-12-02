"""
Volatility-aware audit scheduler for the hybrid funnel telemetry.

Turns daily/weekly compliance reviews into a data-driven routine:

1. Pulls the latest VIX print (fallback to cached values when offline)
2. Chooses a cadence (daily if VIX >= 25, else weekly)
3. Checks telemetry logs for theta-related events
4. (Optional) Queries the McMillan RAG layer for theta drawdown guidance

Usage:
    auditor = VolatilityAuditor()
    directive = auditor.evaluate_schedule()
    if auditor.should_run_now(directive):
        review = auditor.run_review(directive)
        auditor.mark_run(directive)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

try:
    import yfinance as yf
except Exception:  # pragma: no cover - optional dependency
    yf = None  # type: ignore[assignment]

from src.utils.telemetry_summary import load_events

logger = logging.getLogger(__name__)


@dataclass
class AuditDirective:
    frequency: Literal["daily", "weekly"]
    vix_level: float
    reason: str
    interval_days: int
    generated_at: str


class VolatilityAuditor:
    """Decides when to run deeper audits (theta loss reviews, etc.)."""

    def __init__(
        self,
        *,
        telemetry_log: Path | str = Path("data/audit_trail/hybrid_funnel_runs.jsonl"),
        state_path: Path | str = Path("data/audit_trail/vol_auditor_state.json"),
        high_vol_threshold: float = 25.0,
        now: datetime | None = None,
    ) -> None:
        self.telemetry_log = Path(telemetry_log)
        self.state_path = Path(state_path)
        self.high_vol_threshold = high_vol_threshold
        self.now = now or datetime.utcnow()

    # ------------------------------------------------------------------ #
    # Scheduling
    # ------------------------------------------------------------------ #
    def evaluate_schedule(self) -> AuditDirective:
        vix = self._current_vix()
        if vix >= self.high_vol_threshold:
            frequency: Literal["daily", "weekly"] = "daily"
            reason = f"VIX {vix:.1f} >= {self.high_vol_threshold:.0f} ⇒ daily theta audit"
            interval = 1
        else:
            frequency = "weekly"
            reason = f"VIX {vix:.1f} < {self.high_vol_threshold:.0f} ⇒ weekly review"
            interval = 7
        return AuditDirective(
            frequency=frequency,
            vix_level=vix,
            reason=reason,
            interval_days=interval,
            generated_at=self.now.isoformat(),
        )

    def should_run_now(self, directive: AuditDirective) -> bool:
        state = self._load_state()
        last_run = state.get("last_run")
        if not last_run:
            return True
        try:
            last_dt = datetime.fromisoformat(last_run)
        except ValueError:
            return True
        return self.now - last_dt >= timedelta(days=directive.interval_days)

    def mark_run(self, directive: AuditDirective) -> None:
        payload = {"last_run": self.now.isoformat(), "frequency": directive.frequency}
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as exc:  # pragma: no cover - diagnostics only
            logger.warning("Failed to persist volatility auditor state: %s", exc)

    # ------------------------------------------------------------------ #
    # Audit Execution
    # ------------------------------------------------------------------ #
    def run_review(self, directive: AuditDirective) -> dict[str, Any]:
        """Summarize theta telemetry and optionally pull RAG guidance."""
        events = self._load_recent_events()
        theta_events = [
            event
            for event in events
            if "theta" in str(event.get("event", "")).lower()
            or "theta" in str(event.get("ticker", "")).lower()
        ]
        summary = {
            "directive": asdict(directive),
            "theta_events_considered": len(theta_events),
            "recent_theta_events": theta_events[-10:],
            "notes": [],
        }

        try:
            from src.rag.options_book_retriever import OptionsBookRetriever

            retriever = OptionsBookRetriever()
            iv_rank = max(0.0, min(100.0, (directive.vix_level / 40.0) * 100))
            rag = retriever.search_with_iv_regime(
                query="theta loss containment checklist",
                iv_rank=iv_rank,
                top_k=3,
            )
            summary["rag_guidance"] = {
                "iv_rank": iv_rank,
                "answer": rag.get("combined_answer"),
                "book_results": rag.get("book_results", [])[:3],
            }
        except Exception as exc:  # pragma: no cover - optional dependency
            summary["notes"].append(f"RAG guidance unavailable: {exc}")

        return summary

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _current_vix(self) -> float:
        if yf is None:
            return 20.0
        try:
            ticker = yf.Ticker("^VIX")
            hist = ticker.history(period="5d")
            if hist is not None and not hist.empty:
                return float(hist["Close"].iloc[-1])
        except Exception as exc:  # pragma: no cover - network dependency
            logger.debug("Failed to fetch VIX from yfinance: %s", exc)
        return 20.0

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _load_recent_events(self, limit: int = 500) -> list[dict[str, Any]]:
        if not self.telemetry_log.exists():
            return []
        try:
            events = load_events(self.telemetry_log)
        except Exception as exc:
            logger.debug("Failed to load telemetry for auditor: %s", exc)
            return []
        return events[-limit:]
