from enum import Enum
from typing import List, Any

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

class GateStep:
    def __init__(self, name: str, handler=None):
        self.name = name
        self.status = StepStatus.PENDING
        self.handler = handler
        self.error: str = ""
        
    def start(self):
        self.status = StepStatus.RUNNING
        if self.handler:
            try:
                self.handler()
                self.status = StepStatus.COMPLETED
            except Exception as e:
                self.status = StepStatus.FAILED
                self.error = str(e)
        else:
            self.status = StepStatus.COMPLETED

class GateStepResult:
    def __init__(self, step_name: str, success: bool, error: str = ""):
        self.step_name = step_name
        self.success = success
        self.error = error

class GateReport:
    def __init__(self):
        self.steps: List[GateStep] = []
        self.success: bool = False

class AgentHandoffGate:
    def __init__(self):
        self.steps: List[GateStep] = []
        
    def add_step(self, step: GateStep):
        self.steps.append(step)
        
    def execute_step(self, step_name: str) -> GateStepResult:
        step = next((s for s in self.steps if s.name == step_name), None)
        if not step:
            return GateStepResult(step_name, False, error="Step not found")

        try:
            step.start()
            return GateStepResult(step_name, step.status == StepStatus.COMPLETED, step.error)
        except Exception as e:
            return GateStepResult(step_name, False, error=str(e))
            
    def execute_all(self) -> GateReport:
        report = GateReport()
        
        for step in self.steps:
            self.execute_step(step.name)
            
        report.steps = self.steps.copy()
        report.success = all(step.status == StepStatus.COMPLETED for step in self.steps)
        return report