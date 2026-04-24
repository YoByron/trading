"""Agent workflow toolkit for managing agent workflows."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class WorkflowStep:
    """Represents a step in an agent workflow."""
    step_id: str
    agent_name: str
    action: str
    parameters: Dict[str, Any]
    timestamp: datetime


@dataclass
class RetroCapture:
    """Captures retrospective analysis data."""
    workflow_id: str
    steps: List[WorkflowStep]
    success: bool
    duration: float
    insights: Dict[str, Any]


class AgentWorkflowToolkit:
    """Toolkit for managing agent workflows."""

    def __init__(self):
        self.workflows: Dict[str, List[WorkflowStep]] = {}
        self.retro_captures: List[RetroCapture] = []

    def add_workflow_step(self, workflow_id: str, step: WorkflowStep) -> None:
        """Add a step to a workflow."""
        if workflow_id not in self.workflows:
            self.workflows[workflow_id] = []
        self.workflows[workflow_id].append(step)

    def capture_retrospective(self, workflow_id: str, success: bool = True,
                            insights: Optional[Dict[str, Any]] = None) -> RetroCapture:
        """Capture retrospective analysis for a workflow."""
        if insights is None:
            insights = {}

        steps = self.workflows.get(workflow_id, [])
        duration = 0.0  # Calculate duration based on steps if needed

        retro = RetroCapture(
            workflow_id=workflow_id,
            steps=steps,
            success=success,
            duration=duration,
            insights=insights
        )

        self.retro_captures.append(retro)
        return retro

    def get_workflow_steps(self, workflow_id: str) -> List[WorkflowStep]:
        """Get all steps for a workflow."""
        return self.workflows.get(workflow_id, [])