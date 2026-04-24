"""Agent workflow toolkit for managing trading workflows."""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    status: str
    timestamp: datetime
    details: Optional[str] = None


@dataclass
class WorkflowRun:
    """Represents a complete workflow execution."""
    workflow_id: str
    steps: List[WorkflowStep]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"


def build_retro_markdown(workflow_run: WorkflowRun) -> str:
    """Build a retrospective markdown report for a workflow run."""
    lines = []
    lines.append(f"# Workflow Retrospective: {workflow_run.workflow_id}")
    lines.append(f"**Start Time:** {workflow_run.start_time}")
    if workflow_run.end_time:
        lines.append(f"**End Time:** {workflow_run.end_time}")
        duration = workflow_run.end_time - workflow_run.start_time
        lines.append(f"**Duration:** {duration}")
    lines.append(f"**Status:** {workflow_run.status}")
    lines.append("")
    
    lines.append("## Steps")
    for step in workflow_run.steps:
        lines.append(f"- **{step.name}** ({step.status}) - {step.timestamp}")
        if step.details:
            lines.append(f"  - {step.details}")
    
    return "\n".join(lines)


def create_workflow_step(name: str, status: str = "pending", details: str = None) -> WorkflowStep:
    """Create a new workflow step."""
    return WorkflowStep(
        name=name,
        status=status,
        timestamp=datetime.now(),
        details=details
    )


def start_workflow(workflow_id: str) -> WorkflowRun:
    """Start a new workflow run."""
    return WorkflowRun(
        workflow_id=workflow_id,
        steps=[],
        start_time=datetime.now()
    )


def complete_workflow(workflow_run: WorkflowRun, status: str = "completed") -> WorkflowRun:
    """Mark a workflow as completed."""
    workflow_run.end_time = datetime.now()
    workflow_run.status = status
    return workflow_run