"""Agent workflow toolkit for building and managing workflows."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    name: str
    description: str
    action: str
    parameters: Dict[str, Any] = None


@dataclass
class Workflow:
    """A workflow definition."""
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = None


def build_retro_markdown(workflow_data: Dict[str, Any]) -> str:
    """Build retrospective markdown from workflow data."""
    if not workflow_data:
        return "# Workflow Retrospective\n\nNo data available."
    
    markdown = "# Workflow Retrospective\n\n"
    
    if "name" in workflow_data:
        markdown += f"## Workflow: {workflow_data['name']}\n\n"
    
    if "description" in workflow_data:
        markdown += f"**Description:** {workflow_data['description']}\n\n"
    
    if "steps" in workflow_data:
        markdown += "## Steps\n\n"
        for i, step in enumerate(workflow_data["steps"], 1):
            step_name = step.get("name", f"Step {i}")
            markdown += f"### {i}. {step_name}\n\n"
            if "description" in step:
                markdown += f"{step['description']}\n\n"
    
    if "metadata" in workflow_data:
        markdown += "## Metadata\n\n"
        for key, value in workflow_data["metadata"].items():
            markdown += f"- **{key}:** {value}\n"
    
    return markdown


class AgentWorkflowToolkit:
    """Toolkit for managing agent workflows."""
    
    def __init__(self):
        self.workflows = {}
    
    def add_workflow(self, workflow: Workflow):
        """Add a workflow to the toolkit."""
        self.workflows[workflow.name] = workflow
    
    def get_workflow(self, name: str) -> Workflow:
        """Get a workflow by name."""
        return self.workflows.get(name)
    
    def list_workflows(self) -> List[str]:
        """List all workflow names."""
        return list(self.workflows.keys())