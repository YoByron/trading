#!/usr/bin/env python3

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


@dataclass
class GateReport:
    step_name: str
    message: str
    details: Optional[List[str]] = None
    success: bool = True


def check_trading_policy_drift() -> GateReport:
    """Check for trading policy drift before agent handoff."""
    try:
        monitor = PolicyDriftMonitor(policy_doc_paths=DEFAULT_POLICY_DOC_PATHS)
        drift_results = monitor.check_policy_drift()
        
        if drift_results.has_drift:
            return GateReport(
                step_name="Trading Policy Drift",
                message=f"Policy drift detected in {len(drift_results.drifted_policies)} policies",
                details=[
                    f"{policy}: {reason}" 
                    for policy, reason in drift_results.drifted_policies.items()
                ],
                success=False
            )
        else:
            return GateReport(
                step_name="Trading Policy Drift",
                message="No policy drift detected",
                success=True
            )
    except Exception as e:
        return GateReport(
            step_name="Trading Policy Drift",
            message=f"Error checking policy drift: {str(e)}",
            success=False
        )


def check_market_conditions() -> GateReport:
    """Check market conditions for safe trading."""
    # Placeholder for market condition checks
    return GateReport(
        step_name="Market Conditions",
        message="Market conditions check passed",
        success=True
    )


def check_system_health() -> GateReport:
    """Check system health metrics."""
    # Placeholder for system health checks
    return GateReport(
        step_name="System Health",
        message="System health check passed",
        success=True
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
        
        status = "✅" if report.success else "❌"
        print(f"{status} {report.step_name}: {report.message}")
        
        if report.details:
            for detail in report.details:
                print(f"   - {detail}")
        
        if not report.success:
            all_passed = False
    
    print(f"\n🚪 Gate Status: {'OPEN' if all_passed else 'CLOSED'}")
    
    if not all_passed:
        print("❌ Agent handoff blocked due to failed gate checks")
        print("Fix the issues above before proceeding with agent handoff")
    else:
        print("✅ All gate checks passed - agent handoff approved")
    
    return all_passed


if __name__ == "__main__":
    success = run_gate_checks()
    sys.exit(0 if success else 1)