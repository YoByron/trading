from typing import Dict, Any, List, Optional
from datetime import datetime

def build_retro_markdown(workflow_data: Dict[str, Any]) -> str:
    """Build a retrospective markdown report from workflow data."""
    markdown = "# Workflow Retrospective\n\n"
    
    if 'timestamp' in workflow_data:
        markdown += f"**Date:** {workflow_data['timestamp']}\n\n"
    
    if 'workflow_name' in workflow_data:
        markdown += f"## Workflow: {workflow_data['workflow_name']}\n\n"
    
    if 'summary' in workflow_data:
        markdown += f"### Summary\n{workflow_data['summary']}\n\n"
    
    if 'steps' in workflow_data:
        markdown += "### Steps Executed\n"
        for i, step in enumerate(workflow_data['steps'], 1):
            markdown += f"{i}. {step}\n"
        markdown += "\n"
    
    if 'metrics' in workflow_data:
        markdown += "### Metrics\n"
        for metric, value in workflow_data['metrics'].items():
            markdown += f"- **{metric}:** {value}\n"
        markdown += "\n"
    
    if 'outcomes' in workflow_data:
        markdown += f"### Outcomes\n{workflow_data['outcomes']}\n\n"
    
    if 'lessons_learned' in workflow_data:
        markdown += f"### Lessons Learned\n{workflow_data['lessons_learned']}\n\n"
    
    return markdown

class WorkflowToolkit:
    """Toolkit for managing agent workflows."""
    
    def __init__(self):
        self.workflows: List[Dict[str, Any]] = []
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
    
    def start_workflow(self, name: str, config: Dict[str, Any]) -> str:
        """Start a new workflow."""
        workflow_id = f"workflow_{len(self.workflows)}_{datetime.now().timestamp()}"
        workflow = {
            'id': workflow_id,
            'name': name,
            'config': config,
            'start_time': datetime.now().isoformat(),
            'status': 'active',
            'steps': [],
            'metrics': {}
        }
        
        self.workflows.append(workflow)
        self.active_workflows[workflow_id] = workflow
        return workflow_id
    
    def add_step(self, workflow_id: str, step_description: str):
        """Add a step to a workflow."""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]['steps'].append(step_description)
    
    def complete_workflow(self, workflow_id: str, outcomes: str = ""):
        """Complete a workflow."""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow['status'] = 'completed'
            workflow['end_time'] = datetime.now().isoformat()
            workflow['outcomes'] = outcomes
            del self.active_workflows[workflow_id]