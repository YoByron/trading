"""Agent handoff gate for managing trading agent transitions."""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class GateStatus(Enum):
    """Status of gate validation."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class GateStepResult:
    """Result of a single gate validation step."""
    step_name: str
    status: GateStatus
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class GateResult:
    """Overall result of gate validation."""
    gate_id: str
    status: GateStatus
    steps: List[GateStepResult]
    overall_message: str


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
                    status = GateStatus.PASSED if result else GateStatus.FAILED
                    message = f"Step {step['name']} {'passed' if result else 'failed'}"
                    step_result = GateStepResult(
                        step_name=step['name'],
                        status=status,
                        message=message
                    )
                else:
                    step_result = result
                
                steps.append(step_result)
                
                if step_result.status == GateStatus.FAILED:
                    overall_status = GateStatus.FAILED
                elif step_result.status == GateStatus.REQUIRES_REVIEW and overall_status != GateStatus.FAILED:
                    overall_status = GateStatus.REQUIRES_REVIEW
                    
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
            overall_message="Gate validation completed"
        )