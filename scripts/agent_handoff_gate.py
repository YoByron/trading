from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class GateStepResult:
    step_name: str
    passed: bool
    message: str
    data: Dict[str, Any] = None

@dataclass
class GateResult:
    gate_id: str
    passed: bool
    steps: List[GateStepResult]
    message: str

@dataclass
class GateReport:
    gate_id: str
    result: GateResult
    timestamp: str

class AgentHandoffGate:
    def __init__(self, gate_id: str):
        self.gate_id = gate_id

    def validate(self, context: Dict[str, Any]) -> GateResult:
        steps = []

        # Example validation step
        step = GateStepResult(
            step_name="context_check",
            passed=True,
            message="Context validation passed",
            data={}
        )
        steps.append(step)

        return GateResult(
            gate_id=self.gate_id,
            passed=True,
            steps=steps,
            message=f"Gate '{self.gate_id}' validation completed"
        )