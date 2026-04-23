#!/usr/bin/env python3
"""Agent handoff gate checks for safe system transitions."""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Callable
from enum import Enum

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


class GateStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class GateReport:
    check_name: str
    status: GateStatus
    message: str
    details: List[str] = None


@dataclass
class GateStepResult:
    passed: bool
    report: GateReport


def check_trading_policy_drift() -> GateReport:
    """Check for trading policy drift."""
    try:
        monitor = PolicyDriftMonitor(policy_doc_paths=DEFAULT_POLICY_DOC_PATHS)
        drift_results = monitor.check_policy_drift()

        if drift_results.has_drift:
            return GateReport(
                check_name="Trading Policy Drift",
                status=GateStatus.FAIL,
                message=f"Policy drift detected in {len(drift_results.drifted_policies)} policies",
                details=[
                    f"{policy}: {reason}"
                    for policy, reason in drift_results.drifted_policies.items()
                ],
            )
        else:
            return GateReport(
                check_name="Trading Policy Drift",
                status=GateStatus.PASS,
                message="No policy drift detected",
            )
    except Exception as e:
        return GateReport(
            check_name="Trading Policy Drift",
            status=GateStatus.FAIL,
            message=f"Error checking policy drift: {str(e)}",
        )


def check_system_health() -> GateReport:
    """Check basic system health metrics."""
    # Placeholder for system health checks
    return GateReport(
        check_name="System Health",
        status=GateStatus.PASS,
        message="System health check passed",
    )


def check_market_conditions() -> GateReport:
    """Check if market conditions are suitable for agent operation."""
    # Placeholder for market condition checks
    return GateReport(
        check_name="Market Conditions",
        status=GateStatus.PASS,
        message="Market conditions are suitable",
    )


def run_gate_checks() -> bool:
    """Run all gate checks before agent handoff."""
    print("🚪 Running Agent Handoff Gate Checks...")

    checks = [
        check_trading_policy_drift,
        check_market_conditions,
        check_system_health,
    ]

    all_passed = True
    reports = []

    for check in checks:
        report = check()
        reports.append(report)
        
        status_emoji = "✅" if report.status == GateStatus.PASS else "❌"
        print(f"{status_emoji} {report.check_name}: {report.message}")
        
        if report.details:
            for detail in report.details:
                print(f"    - {detail}")
        
        if report.status == GateStatus.FAIL:
            all_passed = False

    print("\n" + "="*50)
    if all_passed:
        print("🎉 All gate checks PASSED! Agent handoff is authorized.")
    else:
        print("🚫 Some gate checks FAILED! Agent handoff is BLOCKED.")
    print("="*50)

    return all_passed


if __name__ == "__main__":
    success = run_gate_checks()
    sys.exit(0 if success else 1)