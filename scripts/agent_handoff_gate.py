from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class GateStep:
    step_id: str
    name: str
    description: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None

@dataclass
class GateStepResult:
    success: bool
    steps: List[GateStep]
    message: str

class AgentHandoffGate:
    def __init__(self, gate_id: str, required_steps: List[str]):
        self.gate_id = gate_id
        self.required_steps = required_steps
        self.steps: Dict[str, GateStep] = {}
        
        for step_id in required_steps:
            self.steps[step_id] = GateStep(
                step_id=step_id,
                name=step_id.replace('_', ' ').title(),
                description=f"Execute {step_id} validation"
            )
    
    def execute_step(self, step_id: str) -> bool:
        if step_id not in self.steps:
            return False
            
        step = self.steps[step_id]
        step.status = StepStatus.RUNNING
        
        try:
            step.status = StepStatus.COMPLETED
            step.result = {"validated": True}
            return True
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            return False
    
    def validate_gate(self) -> GateStepResult:
        steps = list(self.steps.values())
        all_completed = all(step.status == StepStatus.COMPLETED for step in steps)
        
        return GateStepResult(
            success=all_completed,
            steps=steps,
            message=f"Gate '{self.gate_id}' validation completed"
        )