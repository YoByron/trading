from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GateStep:
    step_id: str
    status: StepStatus
    description: str
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class GateStepResult:
    success: bool
    steps: List[GateStep]
    message: str


@dataclass
class GateReport:
    gate_id: str
    result: GateStepResult
    timestamp: datetime


class AgentHandoffGate:
    def __init__(self, gate_id: str, required_steps: List[str]):
        self.gate_id = gate_id
        self.required_steps = required_steps
        self.steps: Dict[str, GateStep] = {}

        for step_id in required_steps:
            self.steps[step_id] = GateStep(
                step_id=step_id,
                status=StepStatus.PENDING,
                description=f"Execute {step_id} validation"
            )

    def execute_step(self, step_id: str) -> bool:
        if step_id not in self.steps:
            return False

        step = self.steps[step_id]
        step.status = StepStatus.RUNNING

        try:
            step.status = StepStatus.COMPLETED
            step.timestamp = datetime.now()
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
            message="Gate validation completed" if all_completed else "Gate validation failed"
        )

    def generate_report(self) -> GateReport:
        result = self.validate_gate()
        return GateReport(
            gate_id=self.gate_id,
            result=result,
            timestamp=datetime.now()
        )


def main():
    gate = AgentHandoffGate("test_gate", ["validation", "security_check"])
    gate.execute_step("validation")
    gate.execute_step("security_check")
    report = gate.generate_report()
    print(f"Gate {report.gate_id}: {'PASSED' if report.result.success else 'FAILED'}")


if __name__ == "__main__":
    main()