#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)

@dataclass
class GateStepResult:
    success: bool
    steps: List[str]
    violations: List[str]

def get_changed_files() -> List[Path]:
    """Get list of changed files from git diff."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT
        )
        changed_files = result.stdout
    except Exception:
        return []

    if not changed_files.strip():
        return []

    paths = []
    for line in changed_files.strip().split('\n'):
        if line.strip():
            file_path = REPO_ROOT / line.strip()
            if file_path.exists():
                paths.append(file_path)
    return paths

def check_policy_drift() -> GateStepResult:
    """Check for policy drift in changed files."""
    changed_files = get_changed_files()
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
            steps.append(f"Analyzing {file_path.relative_to(REPO_ROOT)}")
            violations = monitor.check_file_for_violations(file_path)
            if violations:
                policy_violations.extend(violations)

    if policy_violations:
        steps.append(f"Found {len(policy_violations)} policy violations")
        return GateStepResult(
            success=False,
            steps=steps,
            violations=policy_violations
        )
    else:
        steps.append("No policy violations found")
        return GateStepResult(
            success=True,
            steps=steps,
            violations=[]
        )

def main():
    """Main entry point for agent handoff gate."""
    result = check_policy_drift()
    
    print("Agent Handoff Gate Results:")
    print("=" * 40)
    
    for step in result.steps:
        print(f"✓ {step}")
    
    if not result.success:
        print("\nPolicy Violations:")
        print("-" * 20)
        for violation in result.violations:
            print(f"⚠️  {violation}")
        sys.exit(1)
    else:
        print("\n✅ All checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()