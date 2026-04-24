from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class RetroCapture:
    workflow_id: str
    timestamp: str
    data: Dict[str, Any]

def generate_workflow_retrospective(workflow_data: Dict[str, Any]) -> str:
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
            if "name" in step:
                markdown += f"{i}. **{step['name']}**\n"
            if "description" in step:
                markdown += f"{step['description']}\n\n"

    if "metadata" in workflow_data:
        markdown += "## Metadata\n\n"
        for key, value in workflow_data["metadata"].items():
            markdown += f"- **{key}:** {value}\n"

    return markdown

def capture_workflow_retrospective(workflow_id: str, data: Dict[str, Any]) -> RetroCapture:
    import datetime
    return RetroCapture(
        workflow_id=workflow_id,
        timestamp=datetime.datetime.now().isoformat(),
        data=data
    )