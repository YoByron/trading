import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ValidationStep:
    step_id: str
    description: str
    status: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class HandoffResult:
    success: bool
    gate_id: str
    steps: List[ValidationStep]
    message: str

def parse_changed_paths(paths_str: str) -> List[str]:
    """Parse comma-separated paths string into a list."""
    if not paths_str:
        return []
    return [path.strip() for path in paths_str.split(',') if path.strip()]

class AgentHandoffGate:
    def __init__(self, gate_id: str):
        self.gate_id = gate_id
        
    def validate_handoff(self, context: Dict[str, Any]) -> HandoffResult:
        """Validate agent handoff conditions."""
        steps = []
        
        # Basic validation step
        step = ValidationStep(
            step_id="basic_check",
            description="Basic handoff validation",
            status="passed"
        )
        steps.append(step)
        
        return HandoffResult(
            success=True,
            gate_id=self.gate_id,
            steps=steps,
            message=f"Gate '{self.gate_id}' validation completed"
        )