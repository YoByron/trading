#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Set

REPO_ROOT = Path(__file__).parent.parent.absolute()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


@dataclass
class GateResult:
    success: bool
    message: str
    details: List[str]


@dataclass
class GateReport:
    gate_name: str
    result: GateResult
    timestamp: str


def get_changed_files() -> Set[Path]:
    """Get list of changed files from git diff"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT
        )
        changed_files_str = result.stdout
    except subprocess.CalledProcessError:
        return set()

    if not changed_files_str or changed_files_str.strip() == "":
        return set()

    paths = set()
    for line in changed_files_str.strip().split('\n'):
        if line.strip():
            full_path = REPO_ROOT / line.strip()
            if full_path.exists():
                paths.add(full_path)
    return paths


def check_policy_drift() -> GateResult:
    """Check for policy drift in changed files"""
    try:
        monitor = PolicyDriftMonitor(
            policy_docs=DEFAULT_POLICY_DOC_PATHS,
            output_file=REPO_ROOT / "data" / "policy_drift_analysis.json"
        )

        drift_results = monitor.analyze_drift()

        if drift_results.has_significant_drift:
            return GateResult(
                success=False,
                message="Policy drift detected - handoff blocked",
                details=[
                    f"Overall drift score: {drift_results.overall_drift_score:.3f}",
                    f"Files with significant drift: {len(drift_results.files_with_drift)}",
                    "Review drift analysis in data/policy_drift_analysis.json",
                    "Consider updating policy documents or code alignment"
                ]
            )

        return GateResult(
            success=True,
            message="Policy drift check passed",
            details=[
                f"Overall drift score: {drift_results.overall_drift_score:.3f}",
                "All files within acceptable drift threshold"
            ]
        )

    except Exception as e:
        return GateResult(
            success=False,
            message=f"Policy drift check failed: {str(e)}",
            details=["Check logs for detailed error information"]
        )


def main():
    """Main gate check function"""
    import datetime
    
    gate_result = check_policy_drift()
    
    report = GateReport(
        gate_name="policy_drift_check",
        result=gate_result,
        timestamp=datetime.datetime.now().isoformat()
    )
    
    print(f"Gate Result: {'PASS' if gate_result.success else 'FAIL'}")
    print(f"Message: {gate_result.message}")
    for detail in gate_result.details:
        print(f"  - {detail}")
    
    if not gate_result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()