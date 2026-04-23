#!/usr/bin/env python3
"""
Agent handoff gate for trading system validation.
"""
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


@dataclass
class GateReport:
    """Report from a gate validation step."""
    passed: bool
    message: str
    details: Optional[str] = None


@dataclass
class GateStepResult:
    """Result from executing a gate step."""
    step_name: str
    passed: bool
    message: str
    details: Optional[str] = None


def parse_changed_files(changes_file: Optional[str] = None) -> List[str]:
    """Parse changed file paths from git or environment."""
    changed_paths = []

    if changes_file and os.path.exists(changes_file):
        with open(changes_file, 'r') as f:
            for line in f:
                path = line.strip()
                if path:
                    changed_paths.append(path)
    else:
        # Try git diff if no changes file
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1'],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT
            )
            if result.returncode == 0:
                changed_paths = [p.strip() for p in result.stdout.split('\n') if p.strip()]
        except Exception:
            pass

    return changed_paths


def check_policy_documents() -> GateReport:
    """Verify trading policy documents are intact and accessible."""
    try:
        missing_docs = []

        for doc_path in DEFAULT_POLICY_DOC_PATHS:
            full_path = REPO_ROOT / doc_path
            if not full_path.exists():
                missing_docs.append(str(doc_path))

        if missing_docs:
            return GateReport(
                passed=False,
                message="Missing policy documents",
                details=f"Missing docs: {', '.join(missing_docs)}"
            )

        return GateReport(passed=True, message="All policy documents present")

    except Exception as e:
        return GateReport(
            passed=False,
            message="Error checking policy documents",
            details=str(e)
        )


def run_handoff_gate(changes_file: Optional[str] = None) -> bool:
    """Run the agent handoff gate validation."""
    print("🚪 Running Agent Handoff Gate...")

    changed_files = parse_changed_files(changes_file)
    if changed_files:
        print(f"📝 Detected {len(changed_files)} changed files")

    # Run policy document check
    policy_check = check_policy_documents()
    print(f"📋 Policy documents: {'✅' if policy_check.passed else '❌'} {policy_check.message}")
    if policy_check.details:
        print(f"   Details: {policy_check.details}")

    overall_passed = policy_check.passed

    print(f"\n🎯 Gate Result: {'PASS' if overall_passed else 'FAIL'}")
    return overall_passed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run agent handoff gate validation")
    parser.add_argument("--changes-file", help="File containing list of changed files")

    args = parser.parse_args()

    success = run_handoff_gate(args.changes_file)
    sys.exit(0 if success else 1)