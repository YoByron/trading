"""Agent workflow toolkit for managing trading workflows."""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class WorkflowStep:
    name: str
    status: str
    timestamp: datetime
    details: Optional[str] = None


@dataclass
class WorkflowExecution:
    workflow_id: str
    steps: List[WorkflowStep]
    start_time: datetime
    end_time: Optional[datetime] = None


class RetroCapture:
    """Captures and analyzes workflow execution data for retrospective analysis."""
    
    def __init__(self):
        self.executions: List[WorkflowExecution] = []
    
    def start_capture(self, workflow_id: str) -> WorkflowExecution:
        """Start capturing a new workflow execution."""
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            steps=[],
            start_time=datetime.now()
        )
        self.executions.append(execution)
        return execution
    
    def add_step(self, execution: WorkflowExecution, step: WorkflowStep):
        """Add a step to the workflow execution."""
        execution.steps.append(step)
    
    def complete_capture(self, execution: WorkflowExecution):
        """Mark workflow execution as complete."""
        execution.end_time = datetime.now()
    
    def get_execution_summary(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Get summary of a specific workflow execution."""
        for execution in self.executions:
            if execution.workflow_id == workflow_id:
                return execution
        return None


def create_workflow_step(name: str, status: str, details: Optional[str] = None) -> WorkflowStep:
    """Create a new workflow step."""
    return WorkflowStep(
        name=name,
        status=status,
        timestamp=datetime.now(),
        details=details
    )


def execute_workflow(workflow_id: str, steps: List[str]) -> WorkflowExecution:
    """Execute a workflow with given steps."""
    capture = RetroCapture()
    execution = capture.start_capture(workflow_id)
    
    for step_name in steps:
        step = create_workflow_step(step_name, "completed")
        capture.add_step(execution, step)
    
    capture.complete_capture(execution)
    return execution