#!/usr/bin/env python3

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)

@dataclass
class GateReport:
    """Report from agent handoff gate checks."""
    success: bool
    steps: List[str]
    violations: List[str] = None

    def __post_init__(self):
        if self.violations is None:
            self.violations = []

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
        steps.append("Initializing policy drift monitor")
        monitor = PolicyDriftMonitor(
            policy_doc_paths=DEFAULT_POLICY_DOC_PATHS,
            repo_root=REPO_ROOT
        )
        
        # Check for policy violations
        steps.append("Scanning for policy violations")
        violations_found = monitor.check_violations()
        
        if violations_found:
            violations.extend([str(v) for v in violations_found])
            steps.append(f"Found {len(violations_found)} policy violations")
            return GateReport(
                success=False,
                steps=steps,
                violations=violations
            )
        else:
            steps.append("No policy violations detected")
            return GateReport(
                success=True,
                steps=steps,
                violations=violations
            )
            
    except Exception as e:
        violations.append(f"Error during policy drift check: {str(e)}")
        steps.append("Policy drift check failed with error")
        return GateReport(
            success=False,
            steps=steps,
            violations=violations
        )

def run_gate_checks() -> GateReport:
    """
    Run all agent handoff gate checks.
    
    Returns:
        GateReport: Aggregated results from all checks
    """
    # For now, just run policy drift check
    # Can be extended with additional checks
    return check_policy_drift()

def main():
    """Main entry point for agent handoff gate."""
    result = check_policy_drift()

    print("Agent Handoff Gate Results:")
    print("=" * 40)

    for step in result.steps:
        print(f"✓ {step}")

    if not result.success:
        print("\nPolicy Violations:")
        for violation in result.violations:
            print(f"  ⚠️  {violation}")
        
        print(f"\nGate Status: ❌ BLOCKED ({len(result.violations)} violations)")
        sys.exit(1)
    else:
        print("\nGate Status: ✅ APPROVED")
        sys.exit(0)

if __name__ == "__main__":
    main()