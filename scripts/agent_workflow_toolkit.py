import os
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class WorkflowStep:
    name: str
    status: str
    output: str
    error: str

@dataclass
class RetroCapture:
    timestamp: str
    workflow_id: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any]

def analyze_project_structure(root_path: str) -> Dict[str, Any]:
    """
    Analyze project structure and return a dictionary representation.
    """
    structure = {}

    for root, dirs, files in os.walk(root_path):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

        rel_path = os.path.relpath(root, root_path)
        if rel_path == '.':
            current_dict = structure
        else:
            path_parts = rel_path.split(os.sep)
            current_dict = structure
            for part in path_parts:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]

        # Add files to current directory
        for file in files:
            if not file.startswith('.') and not file.endswith('.pyc'):
                current_dict[file] = 'file'

    return structure

def generate_workflow_summary(workflow_data: Dict[str, Any]) -> str:
    """Generate a summary of workflow execution."""
    if not workflow_data:
        return "No workflow data available"
    
    steps = workflow_data.get('steps', [])
    completed = sum(1 for step in steps if step.get('status') == 'completed')
    failed = sum(1 for step in steps if step.get('status') == 'failed')
    
    summary = f"Workflow completed {completed} steps successfully"
    if failed > 0:
        summary += f", {failed} steps failed"
    
    return summary

def capture_workflow_state(workflow_id: str, steps: List[WorkflowStep]) -> RetroCapture:
    """Capture current workflow state for retrospective analysis."""
    from datetime import datetime
    
    return RetroCapture(
        timestamp=datetime.now().isoformat(),
        workflow_id=workflow_id,
        steps=steps,
        metadata={
            'total_steps': len(steps),
            'completed_steps': sum(1 for s in steps if s.status == 'completed'),
            'failed_steps': sum(1 for s in steps if s.status == 'failed')
        }
    )