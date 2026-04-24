"""Agent handoff gate for workflow transitions"""
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
)

@dataclass
class GateReport:
    gate_id: str
    status: str
    findings: List[str]
    recommendations: List[str]

@dataclass
class GateCheckResult:
    passed: bool
    report: GateReport

@dataclass
class GateStepResult:
    success: bool
    message: str
    data: Dict

def check_policy_drift_gate():
    """Check for policy drift issues"""
    findings = []
    recommendations = []

    # Check if policy documents exist
    for doc_path in DEFAULT_POLICY_DOC_PATHS:
        full_path = REPO_ROOT / doc_path
        if not full_path.exists():
            findings.append(f"Missing policy document: {doc_path}")
            recommendations.append(f"Create or restore {doc_path}")

    passed = len(findings) == 0

    report = GateReport(
        gate_id="policy_drift",
        status="pass" if passed else "fail",
        findings=findings,
        recommendations=recommendations
    )

    return GateCheckResult(
        passed=passed,
        report=report
    )

if __name__ == "__main__":
    result = check_policy_drift_gate()
    print(f"Gate check passed: {result.passed}")
    if not result.passed:
        print("Findings:", result.report.findings)
        print("Recommendations:", result.report.recommendations)