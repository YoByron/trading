"""Agent handoff gate system for trading workflow validation."""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class GateStatus(Enum):
    """Status enumeration for validation gates."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class GateStepResult:
    """Result of a single validation step."""
    step_name: str
    status: GateStatus
    message: str
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class GateResult:
    """Overall result of a validation gate."""
    gate_id: str
    status: GateStatus
    steps: List[GateStepResult]
    summary: str = ""


@dataclass
class GateReport:
    """Report containing gate validation results."""
    gate_id: str
    result: GateResult
    timestamp: str
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}


class AgentHandoffGate:
    """Manages validation gates for agent handoffs in trading workflows."""

    def __init__(self, gate_id: str):
        """Initialize the gate with a unique identifier."""
        self.gate_id = gate_id
        self.validation_steps = []

    def add_validation_step(self, step_name: str, validator_func: callable):
        """Add a validation step to the gate."""
        self.validation_steps.append({
            'name': step_name,
            'validator': validator_func
        })

    def validate(self, context: Dict[str, Any]) -> GateResult:
        """Run all validation steps and return overall result."""
        steps = []
        overall_status = GateStatus.PASSED

        for step in self.validation_steps:
            try:
                result = step['validator'](context)
                if isinstance(result, bool):
                    step_result = GateStepResult(
                        step_name=step['name'],
                        status=GateStatus.PASSED if result else GateStatus.FAILED,
                        message="Validation passed" if result else "Validation failed"
                    )
                else:
                    step_result = result

                steps.append(step_result)

                if step_result.status == GateStatus.FAILED:
                    overall_status = GateStatus.FAILED
                elif step_result.status == GateStatus.WARNING and overall_status == GateStatus.PASSED:
                    overall_status = GateStatus.WARNING

            except Exception as e:
                step_result = GateStepResult(
                    step_name=step['name'],
                    status=GateStatus.FAILED,
                    message=f"Validation error: {str(e)}"
                )
                steps.append(step_result)
                overall_status = GateStatus.FAILED

        return GateResult(
            gate_id=self.gate_id,
            status=overall_status,
            steps=steps,
            summary=f"Gate {self.gate_id} validation completed with status: {overall_status.value}"
        )