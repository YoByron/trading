from enum import Enum
from typing import List

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class GateStep:
    def __init__(self, name: str, handler):
        self.name = name
        self.status = StepStatus.PENDING
        self.handler = handler
        self.error: str = ""

    def start(self):
        self.status = StepStatus.RUNNING

    def complete(self):
        self.status = StepStatus.COMPLETED

    def fail(self, error: str = ""):
        self.status = StepStatus.FAILED
        self.error = error

class GateStepResult:
    def __init__(self, step_name: str, success: bool, error: str = ""):
        self.step_name = step_name
        self.success = success
        self.error = error

class GateReport:
    def __init__(self):
        self.results: List[GateStepResult] = []
        self.success = True

    def add_result(self, result: GateStepResult):
        self.results.append(result)
        if not result.success:
            self.success = False

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
            step.handler()
            step.complete()
            return GateStepResult(step_name, True)
        except Exception as e:
            return GateStepResult(step_name, False, error=str(e))

    def execute_all(self) -> GateReport:
        report = GateReport()
        for step in self.steps:
            result = self.execute_step(step.name)
            report.add_result(result)
            if not result.success:
                break
        return report

def parse_changed_paths(paths_str: str) -> List[str]:
    """Parse changed file paths from string input."""
    if not paths_str:
        return []
    return [path.strip() for path in paths_str.split('\n') if path.strip()]