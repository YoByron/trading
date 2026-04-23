import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    PolicyDriftMonitor,
)

@dataclass
class GateStepResult:
    """Result of a gate validation step"""
    passed: bool
    message: str
    data: Optional[Dict[str, Any]] = None

def check_policy_drift():
    """Check for policy drift in trading policies"""
    monitor = PolicyDriftMonitor()
    
    try:
        drift_score = monitor.calculate_drift_score(DEFAULT_POLICY_DOC_PATHS)
        
        if drift_score > 0.3:
            return GateStepResult(
                passed=False,
                message=f"Policy drift detected: {drift_score:.2f}",
                data={"drift_score": drift_score}
            )
        
        return GateStepResult(
            passed=True,
            message=f"Policy drift check passed: {drift_score:.2f}",
            data={"drift_score": drift_score}
        )
    
    except Exception as e:
        return GateStepResult(
            passed=False,
            message=f"Policy drift check failed: {str(e)}",
            data={"error": str(e)}
        )

def main():
    """Main gate validation function"""
    print("Running agent handoff gate...")
    
    # Check policy drift
    drift_result = check_policy_drift()
    print(f"Policy drift: {drift_result.message}")
    
    if not drift_result.passed:
        print("Gate validation failed!")
        return False
    
    print("Gate validation passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)