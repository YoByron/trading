#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List

# Get repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


@dataclass
class GateStepResult:
    """Result of a gate step check"""
    success: bool
    message: str
    details: List[str]


@dataclass
class GateReport:
    """Gate check report"""
    gate_name: str
    result: GateStepResult
    timestamp: str


def check_policy_drift() -> GateStepResult:
    """Check for policy drift in trading documents"""
    try:
        monitor = PolicyDriftMonitor(policy_doc_paths=DEFAULT_POLICY_DOC_PATHS)
        
        # Check for drift
        drift_results = monitor.check_for_drift()
        
        if drift_results.has_drift:
            return GateStepResult(
                success=False,
                message=f"Policy drift detected: {drift_results.summary}",
                details=drift_results.changes
            )
        else:
            return GateStepResult(
                success=True,
                message="No policy drift detected",
                details=[]
            )
            
    except Exception as e:
        return GateStepResult(
            success=False,
            message=f"Error checking policy drift: {str(e)}",
            details=[str(e)]
        )


def check_repo_status() -> GateStepResult:
    """Check repository status for uncommitted changes"""
    try:
        # Check for uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT
        )
        
        if result.returncode != 0:
            return GateStepResult(
                success=False,
                message="Failed to check git status",
                details=[result.stderr]
            )
        
        if result.stdout.strip():
            changes = result.stdout.strip().split('\n')
            return GateStepResult(
                success=False,
                message="Uncommitted changes detected",
                details=changes
            )
        else:
            return GateStepResult(
                success=True,
                message="Repository is clean",
                details=[]
            )
            
    except Exception as e:
        return GateStepResult(
            success=False,
            message=f"Error checking repository status: {str(e)}",
            details=[str(e)]
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