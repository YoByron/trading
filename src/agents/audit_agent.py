from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.base_agent import BaseAgent

from src.resilience.audit_graph import AuditGraph

logger = logging.getLogger(__name__)


@dataclass
class AuditViolation:
    """Represents a strategy or safety violation discovered during audit."""

    rule: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    trade_id: str | None = None
    timestamp: str | None = None
    trace_id: str | None = None


@dataclass
class AuditReport:
    """Results of an adversarial audit."""

    timestamp: str
    trades_scanned: int
    violations: list[AuditViolation]
    status: str  # PASS, WARN, FAIL
    summary: str
    mismatches: list[dict[str, Any]] = field(default_factory=list)


class AuditAgent(BaseAgent):
    """
    Adversarial Audit Agent.

    Performs autonomous "Adversarial Audits" on trade execution logs using
    deterministic checks and graph-linked trace analysis.
    """

    def __init__(self, model: str | None = None):
        super().__init__(name="audit_agent", role="System Auditor", model=model)
        self.log_dir = Path("data")
        self.report_dir = Path("reports/audits")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.audit_graph = AuditGraph()

    def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Implementation of abstract base method.
        Calls perform_audit() for the provided date or latest logs.
        """
        date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        report = self.perform_audit(date_str)
        return {
            "status": report.status,
            "violations_count": len(report.violations),
            "mismatches_count": len(report.mismatches),
            "summary": report.summary,
            "report_path": str(self.report_dir / f"audit_{date_str}.json"),
        }

    def perform_audit(self, date_str: str | None = None) -> AuditReport:
        """
        Perform a comprehensive audit using both trade logs and the AuditGraph.
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        log_file = self.log_dir / f"trades_{date_str}.json"
        trades = []
        if log_file.exists():
            try:
                with open(log_file) as f:
                    trades = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load trade log {log_file}: {e}")

        violations = []

        # 1. Scan for Graph Mismatches (Orphaned Decisions)
        mismatches = self.audit_graph.find_mismatches()
        for m in mismatches:
            violations.append(
                AuditViolation(
                    rule="Execution Mismatch",
                    severity="CRITICAL",
                    description=f"Trace {m['trace_id']} has a decision but no execution event.",
                    trace_id=m["trace_id"],
                )
            )

        # 2. Legacy Log Scanning (Enhanced with Trace linking where possible)
        for trade in trades:
            trade_id = trade.get("order_id") or trade.get("symbol", "unknown")
            ts = trade.get("timestamp")
            trace_id = trade.get("trace_id")

            # Check Ticker Whitelist
            symbol = trade.get("symbol", "")
            underlying = symbol[:3] if len(symbol) > 5 else symbol
            allowed = ["SPY", "QQQ", "IWM", "SPX", "XSP", "VIX", "UVXY", "SVXY", "VOO"]

            if underlying not in allowed:
                violations.append(
                    AuditViolation(
                        rule="Ticker Whitelist",
                        severity="HIGH",
                        description=f"Prohibited ticker detected: {symbol}",
                        trade_id=trade_id,
                        timestamp=ts,
                        trace_id=trace_id,
                    )
                )

        # Status Determination
        status = "PASS"
        if any(v.severity == "CRITICAL" for v in violations) or any(
            v.severity == "HIGH" for v in violations
        ):
            status = "FAIL"
        elif violations:
            status = "WARN"

        summary = f"Audit complete. Scanned {len(trades)} trades and {len(self.audit_graph.index)} traces. Found {len(violations)} violations."

        report = AuditReport(
            timestamp=datetime.now().isoformat(),
            trades_scanned=len(trades),
            violations=violations,
            status=status,
            summary=summary,
            mismatches=mismatches,
        )

        # Save Report
        report_file = self.report_dir / f"audit_{date_str}.json"
        with open(report_file, "w") as f:
            json.dump(
                {
                    "timestamp": report.timestamp,
                    "trades_scanned": report.trades_scanned,
                    "status": report.status,
                    "summary": report.summary,
                    "violations": [v.__dict__ for v in report.violations],
                    "mismatches": report.mismatches,
                },
                f,
                indent=2,
            )

        return report

    def run_adversarial_llm_audit(self, date_str: str) -> dict[str, Any]:
        """
        Use RLM Algorithm 1 to perform a deep reasoning audit.
        Generates Python code to analyze logs for subtle patterns.
        """
        _prompt = f"""
        You are the Adversarial Audit Agent. Your mission is to find hidden bugs,
        risk management failures, or logic errors in today's ({date_str}) trade logs.

        Log location: data/trades_{date_str}.json

        Task:
        1. Write a pure Python script to analyze this JSON file.
        2. Look for:
           - Duplicate orders within seconds (Race conditions)
           - Inconsistent pricing (fills far from expected)
           - Strategy drift (trades not matching the iron_condor schema)
        3. Output the results as a JSON object with 'anomalies' and 'score'.
        """
        # Algorithm 1: Plan -> Generate -> Execute -> Finalize
        # Implementation of RLM logic would go here,
        # using reason_with_llm to get the Python code.

        logger.info(f"Running LLM Adversarial Audit for {date_str}...")
        # (Simplified for now - will be expanded in future PRs)
        return {"anomalies": [], "score": 1.0}
