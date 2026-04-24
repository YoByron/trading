"""Agent workflow automation toolkit."""

import os
import json
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class RetroCapture:
    """Captures retrospective information about workflow execution."""
    workflow_id: str
    start_time: str
    end_time: str
    status: str
    metrics: Dict[str, Any]
    errors: List[str]
    artifacts: List[str]


@dataclass
class WorkflowStep:
    """Represents a single workflow step."""
    name: str
    command: str
    status: str = "pending"
    output: str = ""
    error: str = ""


@dataclass
class Workflow:
    """Complete workflow definition."""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any]


def create_workflow(name: str, description: str) -> Workflow:
    """Create a new workflow instance."""
    workflow_id = f"wf_{name.lower().replace(' ', '_')}"
    return Workflow(
        id=workflow_id,
        name=name,
        description=description,
        steps=[],
        metadata={"created": "auto", "version": "1.0"}
    )


def add_step(workflow: Workflow, name: str, command: str) -> None:
    """Add a step to a workflow."""
    step = WorkflowStep(name=name, command=command)
    workflow.steps.append(step)


def execute_workflow(workflow: Workflow) -> RetroCapture:
    """Execute a workflow and capture results."""
    import datetime
    
    start_time = datetime.datetime.now().isoformat()
    errors = []
    artifacts = []
    
    for step in workflow.steps:
        try:
            result = subprocess.run(
                step.command,
                shell=True,
                capture_output=True,
                text=True
            )
            step.status = "completed" if result.returncode == 0 else "failed"
            step.output = result.stdout
            step.error = result.stderr
            
            if result.returncode != 0:
                errors.append(f"Step '{step.name}' failed: {result.stderr}")
                
        except Exception as e:
            step.status = "error"
            step.error = str(e)
            errors.append(f"Step '{step.name}' error: {e}")
    
    end_time = datetime.datetime.now().isoformat()
    overall_status = "success" if not errors else "failed"
    
    return RetroCapture(
        workflow_id=workflow.id,
        start_time=start_time,
        end_time=end_time,
        status=overall_status,
        metrics={"total_steps": len(workflow.steps), "errors": len(errors)},
        errors=errors,
        artifacts=artifacts
    )


def save_workflow(workflow: Workflow, filepath: str) -> None:
    """Save workflow to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(asdict(workflow), f, indent=2)


def load_workflow(filepath: str) -> Workflow:
    """Load workflow from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    steps = [WorkflowStep(**step_data) for step_data in data['steps']]
    return Workflow(
        id=data['id'],
        name=data['name'],
        description=data['description'],
        steps=steps,
        metadata=data.get('metadata', {})
    )