from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class GateStepResult:
    step_id: str
    success: bool
    message: str
    data: Dict[str, Any] = None

@dataclass 
class GateResult:
    gate_id: str
    success: bool
    steps: List[GateStepResult]
    message: str

class AgentHandoffGate:
    def __init__(self, gate_id: str):
        self.gate_id = gate_id
    
    def validate(self, context: Dict[str, Any]) -> GateResult:
        steps = []
        
        # Example validation step
        step = GateStepResult(
            step_id="basic_validation",
            success=True,
            message="Basic validation passed"
        )
        steps.append(step)
        
        return GateResult(
            gate_id=self.gate_id,
            success=all(step.success for step in steps),
            steps=steps,
            message=f"Gate '{self.gate_id}' validation completed"
        )