#!/usr/bin/env python3

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


@dataclass
class GateReport:
    passed: bool
    policy_violations: List[str]
    steps: List[str]


def parse_changed_paths(changed_files: str) -> List[Path]:
    """Parse changed file paths from git diff output."""
    if not changed_files.strip():
        return []
    
    paths = []
    for line in changed_files.strip().split('\n'):
        if line.strip():
            paths.append(Path(line.strip()))
    return paths


def run_policy_gate(changed_files: List[Path]) -> GateReport:
    """Run policy drift checks on changed files."""
    steps = []
    policy_violations = []
    
    steps.append("Initializing policy drift monitor")
    monitor = PolicyDriftMonitor(
        policy_doc_paths=DEFAULT_POLICY_DOC_PATHS,
        repo_root=REPO_ROOT
    )
    
    steps.append(f"Checking {len(changed_files)} changed files for policy violations")
    
    for file_path in changed_files:
        if file_path.suffix == '.py':
            steps.append(f"Analyzing {file_path}")
            violations = monitor.check_file_for_violations(file_path)
            if violations:
                policy_violations.extend(violations)
    
    if policy_violations:
        steps.append(f"Found {len(policy_violations)} policy violations")
        for violation in policy_violations:
            steps.append(f"  - {violation}")
    else:
        steps.append("No policy violations found")
    
    passed = len(policy_violations) == 0

    return GateReport(
        passed=passed,
        policy_violations=policy_violations,
        steps=steps
    )


def main():
    """Main entry point for the agent handoff gate."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run agent handoff gate checks")
    parser.add_argument("changed_files", nargs="*", help="List of changed files")
    args = parser.parse_args()
    
    changed_paths = [Path(f) for f in args.changed_files]
    report = run_policy_gate(changed_paths)
    
    print("Agent Handoff Gate Report")
    print("=" * 25)
    
    for step in report.steps:
        print(f"  {step}")
    
    if report.passed:
        print("\n✅ Gate PASSED - No policy violations found")
        sys.exit(0)
    else:
        print(f"\n❌ Gate FAILED - {len(report.policy_violations)} violations found")
        sys.exit(1)


if __name__ == "__main__":
    main()