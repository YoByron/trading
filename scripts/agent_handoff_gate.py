#!/usr/bin/env python3

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

# Add the project root to Python path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)

@dataclass
class GateStepResult:
    """Result of a single gate check step"""
    step_name: str
    success: bool
    message: str
    details: dict = None

@dataclass
class GateReport:
    """Report from the agent handoff gate checks"""
    success: bool
    message: str
    steps: List[str]
    violations: List[str]

def check_policy_drift() -> GateReport:
    """
    Check for policy drift using the PolicyDriftMonitor.

    Returns:
        GateReport: Success status and details of the check
    """
    steps = []
    violations = []

    try:
        # Initialize the policy drift monitor
        steps.append("Initializing PolicyDriftMonitor")
        monitor = PolicyDriftMonitor(
            policy_docs=DEFAULT_POLICY_DOC_PATHS,
            repo_root=REPO_ROOT
        )

        # Check for policy violations
        steps.append("Scanning for policy violations")
        violations_found = monitor.check_violations()

        if violations_found:
            violations.extend([str(v) for v in violations_found])
            return GateReport(
                success=False,
                message=f"Found {len(violations_found)} policy violations",
                steps=steps,
                violations=violations
            )
        else:
            return GateReport(
                success=True,
                message="No policy violations found",
                steps=steps,
                violations=violations
            )

    except Exception as e:
        return GateReport(
            success=False,
            message=f"Error during policy drift check: {str(e)}",
            steps=steps,
            violations=violations
        )

def main():
    """Main entry point for the agent handoff gate."""
    print("🔍 Running agent handoff gate checks...")
    
    # Run policy drift check
    policy_result = check_policy_drift()
    
    if not policy_result.success:
        print("❌ Policy drift check failed:")
        print(f"   {policy_result.message}")
        for violation in policy_result.violations:
            print(f"   - {violation}")
        sys.exit(1)
    else:
        print("✅ Policy drift check passed")
    
    print("🎉 All gate checks passed!")

if __name__ == "__main__":
    main()