import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List
from enum import Enum

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)


class GateStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class GateReport:
    check_name: str
    status: GateStatus
    message: str
    details: List[str] = None


def parse_changed_paths(changes_file: str = None) -> List[str]:
    """Parse changed file paths from git or environment."""
    changed_paths = []
    
    if changes_file and os.path.exists(changes_file):
        with open(changes_file, 'r') as f:
            changed_paths = [line.strip() for line in f if line.strip()]
    else:
        # Fallback to git diff
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT
            )
            if result.returncode == 0:
                changed_paths = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        except Exception:
            pass
    
    return changed_paths


def check_policy_document_integrity() -> GateReport:
    """Verify trading policy documents are intact and accessible."""
    try:
        monitor = PolicyDriftMonitor()
        missing_docs = []
        
        for doc_path in DEFAULT_POLICY_DOC_PATHS:
            full_path = REPO_ROOT / doc_path
            if not full_path.exists():
                missing_docs.append(str(doc_path))
        
        if missing_docs:
            return GateReport(
                check_name="Policy Document Integrity",
                status=GateStatus.FAIL,
                message=f"Missing {len(missing_docs)} policy documents",
                details=missing_docs
            )
        
        return GateReport(
            check_name="Policy Document Integrity",
            status=GateStatus.PASS,
            message="All policy documents found and accessible"
        )
    
    except Exception as e:
        return GateReport(
            check_name="Policy Document Integrity",
            status=GateStatus.FAIL,
            message=f"Error checking policy documents: {str(e)}"
        )


def check_critical_file_changes() -> GateReport:
    """Check if critical trading files have been modified."""
    critical_patterns = [
        "src/safety/",
        "src/trading/",
        "config/trading_limits.yaml",
        "config/risk_parameters.yaml"
    ]
    
    changed_paths = parse_changed_paths()
    critical_changes = []
    
    for path in changed_paths:
        if any(pattern in path for pattern in critical_patterns):
            critical_changes.append(path)
    
    if critical_changes:
        return GateReport(
            check_name="Critical File Changes",
            status=GateStatus.WARNING,
            message=f"Found {len(critical_changes)} critical file changes",
            details=critical_changes
        )
    
    return GateReport(
        check_name="Critical File Changes",
        status=GateStatus.PASS,
        message="No critical trading files modified"
    )


def run_gate_checks() -> bool:
    """Run all gate checks and return True if all pass."""
    print("🚪 Running Agent Handoff Gate Checks...")
    print("=" * 50)
    
    checks = [
        check_policy_document_integrity,
        check_critical_file_changes,
    ]
    
    reports = []
    all_passed = True
    
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
    
    print("=" * 50)
    if all_passed:
        print("🎉 All gate checks passed! Handoff approved.")
    else:
        print("❌ Gate checks failed. Please address issues before handoff.")
    
    return all_passed


if __name__ == "__main__":
    success = run_gate_checks()
    sys.exit(0 if success else 1)