from enum import Enum
from typing import Dict, List, Any

class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class GateStep:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None

    def start(self):
        self.status = StepStatus.IN_PROGRESS

    def complete(self, result=None):
        self.status = StepStatus.COMPLETED
        self.result = result

    def fail(self, error: str):
        self.status = StepStatus.FAILED
        self.error = error

class GateStepResult:
    def __init__(self, step_name: str, success: bool, data: Any = None, error: str = None):
        self.step_name = step_name
        self.success = success
        self.data = data
        self.error = error

class HandoffReport:
    def __init__(self):
        self.steps: List[GateStep] = []
        self.success = False
        self.timestamp = None

class AgentHandoffGate:
    def __init__(self):
        self.steps: List[GateStep] = []
        self.current_step_index = 0

    def add_step(self, step: GateStep):
        self.steps.append(step)

    def execute_step(self, step_name: str) -> GateStepResult:
        step = next((s for s in self.steps if s.name == step_name), None)
        if not step:
            return GateStepResult(step_name, False, error="Step not found")
        
        try:
            step.start()
            result = self._process_step(step)
            step.complete(result)
            return GateStepResult(step_name, True, result)
        except Exception as e:
            step.fail(str(e))
            return GateStepResult(step_name, False, error=str(e))

    def _process_step(self, step: GateStep) -> Any:
        return {"processed": True, "step": step.name}

    def get_report(self) -> HandoffReport:
        report = HandoffReport()
        report.steps = self.steps.copy()
        report.success = all(step.status == StepStatus.COMPLETED for step in self.steps)
        return report