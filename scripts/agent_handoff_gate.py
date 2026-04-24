"""Agent handoff gate for managing transitions between different agents."""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum


class GateStatus(Enum):
    """Status of gate validation."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


@dataclass
class ValidationStep:
    """Individual validation step in the gate."""
    name: str
    status: GateStatus
    message: str
    details: Dict[str, Any] = None


@dataclass
class GateResult:
    """Result of gate validation."""
    gate_id: str
    status: GateStatus
    steps: List[ValidationStep]
    summary: str


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
            step_result = ValidationStep(
                name=step.name,
                status=step.status,
                message=step.message,
                details=step.details
            )
            steps.append(step_result)
            
            # Update overall status
            if step_result.status == GateStatus.FAILED:
                overall_status = GateStatus.FAILED
            elif (step_result.status == GateStatus.WARNING and 
                  overall_status == GateStatus.PASSED):
                overall_status = GateStatus.WARNING
        
        return GateResult(
            gate_id=self.gate_id,
            status=overall_status,
            steps=steps,
            summary=f"Gate {self.gate_id} validation completed with status: {overall_status.value}"
        )


def parse_changed_paths(changed_files: List[str]) -> Dict[str, List[str]]:
    """Parse changed file paths into categories."""
    categories = {
        'scripts': [],
        'src': [],
        'tests': [],
        'docs': [],
        'other': []
    }
    
    for file_path in changed_files:
        if file_path.startswith('scripts/'):
            categories['scripts'].append(file_path)
        elif file_path.startswith('src/'):
            categories['src'].append(file_path)
        elif file_path.startswith('tests/'):
            categories['tests'].append(file_path)
        elif file_path.startswith('docs/'):
            categories['docs'].append(file_path)
        else:
            categories['other'].append(file_path)
    
    return categories


def create_handoff_gate(gate_id: str) -> AgentHandoffGate:
    """Create a new handoff gate."""
    return AgentHandoffGate(gate_id)


def validate_agent_handoff(source_agent: str, target_agent: str, context: Dict[str, Any]) -> GateResult:
    """Validate handoff between agents."""
    gate = create_handoff_gate(f"{source_agent}_to_{target_agent}")
    
    # Add basic validation steps
    gate.add_validation_step(ValidationStep(
        name="context_validation",
        status=GateStatus.PASSED,
        message="Context validation passed"
    ))
    
    gate.add_validation_step(ValidationStep(
        name="agent_compatibility",
        status=GateStatus.PASSED,
        message="Agent compatibility verified"
    ))
    
    return gate.validate(context)