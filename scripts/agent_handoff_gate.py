import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)

@dataclass
class GateStepResult:
    """Result of a gate step execution."""
    step_name: str
    success: bool
    message: str
    data: Optional[Dict] = None

@dataclass
class GateReport:
    """Report from gate validation."""
    passed: bool
    warnings: List[str]
    policy_violations: List[str]
    steps: List[GateStepResult]

class AgentHandoffGate:
    """Gate to validate agent handoffs and policy compliance."""

    def __init__(self, policy_paths: Optional[List[Path]] = None):
        self.policy_paths = policy_paths or DEFAULT_POLICY_DOC_PATHS
        self.drift_monitor = PolicyDriftMonitor(self.policy_paths)

    def validate_handoff(self, context: Dict) -> GateReport:
        """Validate an agent handoff request."""
        steps = []
        warnings = []
        policy_violations = []

        # Check for policy drift
        drift_result = self.drift_monitor.check_drift()
        drift_detected = drift_result.drift_detected

        if drift_detected:
            policy_violations.extend(drift_result.violations)

        step_result = GateStepResult(
            step_name="policy_drift_check",
            success=not drift_detected,
            message=f"Policy drift {'detected' if drift_detected else 'not detected'}",
            data={"violations": drift_result.violations}
        )
        steps.append(step_result)

        passed = len(policy_violations) == 0
        
        return GateReport(
            passed=passed,
            warnings=warnings,
            policy_violations=policy_violations,
            steps=steps
        )