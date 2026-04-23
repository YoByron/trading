import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)

@dataclass
class GateReport:
    """Report from the agent handoff gate analysis."""
    passed: bool
    errors: List[str]
    warnings: List[str]
    drift_detected: bool
    policy_violations: List[str]

@dataclass
class AgentHandoffGate:
    """Gate to validate agent handoffs and policy compliance."""
    
    def __init__(self, policy_paths: Optional[List[Path]] = None):
        self.policy_paths = policy_paths or DEFAULT_POLICY_DOC_PATHS
        self.drift_monitor = PolicyDriftMonitor(self.policy_paths)
    
    def validate_handoff(self, context: Dict) -> GateReport:
        """Validate an agent handoff request."""
        errors = []
        warnings = []
        policy_violations = []
        
        # Check for policy drift
        drift_result = self.drift_monitor.check_drift()
        drift_detected = drift_result.drift_detected
        
        if drift_detected:
            policy_violations.extend(drift_result.violations)
        
        # Validate context completeness
        required_fields = ['agent_id', 'target_agent', 'task', 'risk_level']
        for field in required_fields:
            if field not in context:
                errors.append(f"Missing required field: {field}")
        
        # Check risk level
        if 'risk_level' in context:
            risk_level = context['risk_level']
            if risk_level not in ['low', 'medium', 'high']:
                errors.append(f"Invalid risk level: {risk_level}")
            elif risk_level == 'high':
                warnings.append("High risk handoff requires additional approval")
        
        passed = len(errors) == 0 and not drift_detected
        
        return GateReport(
            passed=passed,
            errors=errors,
            warnings=warnings,
            drift_detected=drift_detected,
            policy_violations=policy_violations
        )

def main() -> bool:
    """Main entry point for the agent handoff gate."""
    gate = AgentHandoffGate()
    
    # Example validation
    test_context = {
        'agent_id': 'test_agent',
        'target_agent': 'execution_agent',
        'task': 'execute_trade',
        'risk_level': 'medium'
    }
    
    report = gate.validate_handoff(test_context)
    
    print(f"Gate validation: {'PASSED' if report.passed else 'FAILED'}")
    if report.errors:
        print("Errors:", report.errors)
    if report.warnings:
        print("Warnings:", report.warnings)
    if report.drift_detected:
        print("Policy drift detected:", report.policy_violations)
    
    return report.passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)