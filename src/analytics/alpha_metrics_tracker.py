"""
Alpha Metrics Tracker - Advanced tracking for high-alpha gates and regime performance.

This component tracks:
1. Defense Alpha: P/L prevented by blocking low-probability trades.
2. Regime Drift: How market conditions are shifting relative to our 'High-Alpha' windows.
3. ML Alignment: Correlation between RAG lessons and ML policy decisions.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
ALPHA_METRICS_PATH = PROJECT_ROOT / "data" / "alpha_metrics.json"

class AlphaMetricsTracker:
    def __init__(self, repo_root: Path = PROJECT_ROOT):
        self.repo_root = repo_root
        self.metrics_file = repo_root / "data" / "alpha_metrics.json"
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> Dict[str, Any]:
        if self.metrics_file.exists():
            try:
                return json.loads(self.metrics_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load metrics: {e}")
                return self._default_metrics()
        return self._default_metrics()

    def _default_metrics(self) -> Dict[str, Any]:
        return {
            "last_updated": datetime.now().isoformat(),
            "defense_alpha": {
                "blocked_trades_total": 0,
                "thursday_gate_blocks": 0,
                "dte_gate_blocks": 0,
                "vix_gate_blocks": 0,
                "estimated_loss_prevented": 0.0
            },
            "regime_performance": {
                "thursday_win_rate": 0.0,
                "monday_win_rate": 0.0,
                "other_days_win_rate": 0.0
            },
            "ml_alignment": {
                "rag_penalties_applied": 0,
                "policy_compliance_rate": 0.0
            }
        }

    def record_block(self, gate_type: str, estimated_loss: float = 0.0):
        """Record a trade blocked by our safety gates."""
        self.metrics["defense_alpha"]["blocked_trades_total"] += 1
        key = f"{gate_type.lower()}_gate_blocks"
        if key in self.metrics["defense_alpha"]:
            self.metrics["defense_alpha"][key] += 1
        self.metrics["defense_alpha"]["estimated_loss_prevented"] += estimated_loss
        self.save()

    def update_regime_stats(self, trades: List[Dict[str, Any]]):
        """Calculate win rates by weekday to verify the alpha anomaly."""
        thursday_trades = [t for t in trades if self._get_weekday(t.get('entry_date')) == 3]
        monday_trades = [t for t in trades if self._get_weekday(t.get('entry_date')) == 0]
        other_trades = [t for t in trades if self._get_weekday(t.get('entry_date')) not in [0, 3]]

        self.metrics["regime_performance"]["thursday_win_rate"] = self._win_rate(thursday_trades)
        self.metrics["regime_performance"]["monday_win_rate"] = self._win_rate(monday_trades)
        self.metrics["regime_performance"]["other_days_win_rate"] = self._win_rate(other_trades)
        self.save()

    def _get_weekday(self, date_str: str) -> int:
        try:
            return datetime.fromisoformat(date_str).weekday()
        except (ValueError, TypeError):
            return -1

    def _win_rate(self, trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0
        wins = len([t for t in trades if t.get('outcome') == 'win' or t.get('realized_pnl', 0) > 0])
        return round((wins / len(trades)) * 100, 2)

    def save(self):
        self.metrics["last_updated"] = datetime.now().isoformat()
        self.metrics_file.write_text(json.dumps(self.metrics, indent=2))

if __name__ == "__main__":
    # Self-test / Initial scan
    tracker = AlphaMetricsTracker()
    trades_file = PROJECT_ROOT / "data" / "trades.json"
    if trades_file.exists():
        trades_data = json.loads(trades_file.read_text())
        tracker.update_regime_stats(trades_data.get("trades", []))
    print(f"Alpha Metrics Updated: {tracker.metrics_file}")
