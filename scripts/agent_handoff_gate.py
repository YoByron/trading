"""Agent handoff gate for workflow transitions"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
)

@dataclass
class GateReport:
    """Report from gate analysis"""
    gate_id: str
    status: str
    findings: List[str]
    recommendations: List[str]

@dataclass
class GateCheckResult:
    """Result of a gate check operation"""
    passed: bool
    gate_report: GateReport
    metadata: Dict

def run_policy_drift_check() -> GateCheckResult:
    """Run policy drift analysis"""
    findings = []
    recommendations = []
    
    # Check if policy documents exist
    for doc_path in DEFAULT_POLICY_DOC_PATHS:
        if not Path(doc_path).exists():
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
        gate_report=report,
        metadata={"check_type": "policy_drift"}
    )

def analyze_handoff_readiness(agent_context: Dict) -> GateCheckResult:
    """Analyze if agent is ready for handoff"""
    findings = []
    recommendations = []
    
    # Check required context fields
    required_fields = ["agent_id", "workflow_state", "completion_status"]
    for field in required_fields:
        if field not in agent_context:
            findings.append(f"Missing required field: {field}")
            recommendations.append(f"Ensure {field} is set in agent context")
    
    passed = len(findings) == 0
    
    report = GateReport(
        gate_id="handoff_readiness",
        status="pass" if passed else "fail",
        findings=findings,
        recommendations=recommendations
    )
    
    return GateCheckResult(
        passed=passed,
        gate_report=report,
        metadata={"agent_id": agent_context.get("agent_id")}
    )

def main():
    """Main execution"""
    # Run policy drift check
    policy_result = run_policy_drift_check()
    print(f"Policy drift check: {policy_result.gate_report.status}")
    
    # Example handoff readiness check
    sample_context = {
        "agent_id": "test_agent",
        "workflow_state": "completed",
        "completion_status": "success"
    }
    handoff_result = analyze_handoff_readiness(sample_context)
    print(f"Handoff readiness: {handoff_result.gate_report.status}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())