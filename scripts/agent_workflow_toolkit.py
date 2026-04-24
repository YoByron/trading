"""Agent workflow toolkit for trading system automation."""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    step_id: str
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None


@dataclass
class Workflow:
    """Workflow definition."""
    workflow_id: str
    name: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = None


@dataclass
class ContextBundle:
    """Bundle of context data for workflow execution."""
    primary: Workflow
    related: List[Dict[str, Any]]
    metadata: Dict[str, Any]


def build_context_bundle(primary_context: Dict[str, Any],
                        related_data: List[Dict[str, Any]] = None) -> ContextBundle:
    """Build a context bundle from primary context and related data."""
    if related_data is None:
        related_data = []

    primary = Workflow(
        workflow_id=primary_context.get('workflow_id', 'default'),
        name=primary_context.get('name', 'Default Workflow'),
        steps=primary_context.get('steps', []),
        metadata=primary_context.get('metadata', {})
    )

    return ContextBundle(
        primary=primary,
        related=related_data,
        metadata=primary_context.get('bundle_metadata', {})
    )


@dataclass
class RetroCapture:
    """Capture retrospective data from workflow execution."""
    execution_id: str
    workflow_id: str
    captured_data: Dict[str, Any]
    timestamp: str
    status: str


def create_retro_capture(execution_id: str, workflow_id: str, data: Dict[str, Any]) -> RetroCapture:
    """Create a retrospective capture."""
    from datetime import datetime
    
    return RetroCapture(
        execution_id=execution_id,
        workflow_id=workflow_id,
        captured_data=data,
        timestamp=datetime.now().isoformat(),
        status="captured"
    )


def execute_workflow_step(step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single workflow step."""
    return {
        'step_id': step.step_id,
        'status': 'completed',
        'result': f"Executed {step.action}",
        'context_updates': {}
    }


def validate_workflow_dependencies(workflow: Workflow) -> bool:
    """Validate that workflow dependencies are satisfied."""
    step_ids = {step.step_id for step in workflow.steps}
    
    for step in workflow.steps:
        if step.dependencies:
            for dep in step.dependencies:
                if dep not in step_ids:
                    return False
    
    return True