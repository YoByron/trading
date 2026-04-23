#!/usr/bin/env python3
"""
Agent Handoff Gate - Validates code changes before agent handoffs
"""

import subprocess
import sys
from pathlib import Path
from typing import List, NamedTuple

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


class GateStepResult(NamedTuple):
    passed: bool
    step_name: str
    message: str
    details: List[str]


def check_trading_policy_drift() -> GateStepResult:
    """Check if trading policies have drifted from documented standards."""
    try:
        monitor = PolicyDriftMonitor(policy_doc_paths=DEFAULT_POLICY_DOC_PATHS)

        # Check for drift
        drift_results = monitor.check_for_drift()

        if drift_results.has_drift:
            return GateStepResult(
                passed=False,
                step_name="Trading Policy Drift",
                message=f"Policy drift detected in {len(drift_results.drifted_policies)} policies",
                details=[f"{policy}: {reason}" for policy, reason in drift_results.drifted_policies.items()]
            )
        else:
            return GateStepResult(
                passed=True,
                step_name="Trading Policy Drift",
                message="No policy drift detected",
                details=[]
            )

    except Exception as e:
        return GateStepResult(
            passed=False,
            step_name="Trading Policy Drift",
            message=f"Error checking policy drift: {str(e)}",
            details=[]
        )


def check_uncommitted_changes() -> GateStepResult:
    """Check if there are uncommitted changes in the repository."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT
        )

        if result.returncode != 0:
            return GateStepResult(
                passed=False,
                step_name="Uncommitted Changes",
                message="Failed to check git status",
                details=[result.stderr]
            )

        if result.stdout.strip():
            changes = result.stdout.strip().split('\n')
            return GateStepResult(
                passed=False,
                step_name="Uncommitted Changes",
                message=f"Found {len(changes)} uncommitted changes",
                details=changes
            )
        else:
            return GateStepResult(
                passed=True,
                step_name="Uncommitted Changes",
                message="No uncommitted changes",
                details=[]
            )

    except Exception as e:
        return GateStepResult(
            passed=False,
            step_name="Uncommitted Changes",
            message=f"Error checking uncommitted changes: {str(e)}",
            details=[]
        )


def parse_changed_paths(git_diff_output: str) -> List[str]:
    """Parse git diff output to extract changed file paths."""
    paths = []
    for line in git_diff_output.strip().split('\n'):
        if line.startswith('+++') or line.startswith('---'):
            # Extract path from diff header
            if line.startswith('+++') and not line.endswith('/dev/null'):
                path = line[4:]  # Remove '+++ '
                if path.startswith('b/'):
                    path = path[2:]  # Remove 'b/' prefix
                paths.append(path)
    return list(set(paths))  # Remove duplicates


def run_gate_checks() -> bool:
    """Run all gate checks and return True if all pass."""
    checks = [
        check_trading_policy_drift,
        check_uncommitted_changes,
    ]

    all_passed = True
    for check in checks:
        result = check()
        print(f"[{'PASS' if result.passed else 'FAIL'}] {result.step_name}: {result.message}")
        if result.details:
            for detail in result.details:
                print(f"  - {detail}")
        if not result.passed:
            all_passed = False

    return all_passed


if __name__ == "__main__":
    success = run_gate_checks()
    sys.exit(0 if success else 1)