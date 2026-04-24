"""Agent handoff gate for validation."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class GateStatus(Enum):
    """Gate validation status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class ValidationStep:
    """A single validation step."""
    name: str
    description: str
    required: bool = True


@dataclass
class StepResult:
    """Result of a validation step."""
    step_name: str
    status: GateStatus
    message: str
    details: Dict[str, Any] = None


@dataclass
class GateResult:
    """Result of gate validation."""
    gate_id: str
    status: GateStatus
    steps: List[StepResult]
    message: str


@dataclass
class GateReport:
    """Report of gate validation results."""
    gate_id: str
    timestamp: str
    result: GateResult
    metadata: Dict[str, Any] = None


class AgentHandoffGate:
    """Gate for validating agent handoffs."""

    def __init__(self, gate_id: str):
        self.gate_id = gate_id
        self.validation_steps = []

    def add_validation_step(self, step: ValidationStep):
        """Add a validation step to the gate."""
        self.validation_steps.append(step)

    def validate(self, context: Dict[str, Any]) -> GateResult:
        """Validate the gate with given context."""
        steps = []
        overall_status = GateStatus.PASSED

        for step in self.validation_steps:
            # Simulate validation logic
            step_result = StepResult(
                step_name=step.name,
                status=GateStatus.PASSED,  # Simplified for now
                message=f"Step '{step.name}' completed successfully",
                details={}
            )
            steps.append(step_result)

            # Update overall status
            if step_result.status == GateStatus.FAILED:
                overall_status = GateStatus.FAILED
            elif (step_result.status == GateStatus.WARNING and
                  overall_status != GateStatus.FAILED):
                overall_status = GateStatus.WARNING

        return GateResult(
            gate_id=self.gate_id,
            status=overall_status,
            steps=steps,
            message=f"Gate '{self.gate_id}' validation completed"
        )