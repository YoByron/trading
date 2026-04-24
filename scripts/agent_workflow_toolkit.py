import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class WorkflowStep:
    name: str
    status: str
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class RetroCapture:
    workflow_id: str
    steps: List[WorkflowStep]
    overall_status: str
    created_at: str
    metadata: Dict[str, Any]

class AgentWorkflowToolkit:
    """Toolkit for managing agent workflows"""
    
    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = workspace_dir
        self.retro_captures: List[RetroCapture] = []
        
    def create_workflow_step(self, name: str, status: str = "PENDING", 
                           metadata: Optional[Dict[str, Any]] = None) -> WorkflowStep:
        """Create a new workflow step"""
        return WorkflowStep(
            name=name,
            status=status,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
    
    def capture_retro(self, workflow_id: str, steps: List[WorkflowStep], 
                     overall_status: str = "COMPLETED", 
                     metadata: Optional[Dict[str, Any]] = None) -> RetroCapture:
        """Capture a retrospective of workflow execution"""
        retro = RetroCapture(
            workflow_id=workflow_id,
            steps=steps,
            overall_status=overall_status,
            created_at=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        self.retro_captures.append(retro)
        return retro
    
    def save_retro_capture(self, retro: RetroCapture, filepath: str) -> None:
        """Save retrospective capture to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(asdict(retro), f, indent=2)
    
    def load_retro_capture(self, filepath: str) -> RetroCapture:
        """Load retrospective capture from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        steps = [WorkflowStep(**step) for step in data['steps']]
        return RetroCapture(
            workflow_id=data['workflow_id'],
            steps=steps,
            overall_status=data['overall_status'],
            created_at=data['created_at'],
            metadata=data['metadata']
        )

def create_workflow_toolkit(workspace_dir: str = "workspace") -> AgentWorkflowToolkit:
    """Factory function to create workflow toolkit"""
    return AgentWorkflowToolkit(workspace_dir)

def main():
    """Main function for testing the toolkit"""
    toolkit = create_workflow_toolkit()
    
    # Example usage
    step1 = toolkit.create_workflow_step("Initialize", "COMPLETED")
    step2 = toolkit.create_workflow_step("Process Data", "COMPLETED") 
    step3 = toolkit.create_workflow_step("Generate Report", "COMPLETED")
    
    retro = toolkit.capture_retro("test_workflow", [step1, step2, step3])
    print(f"Created retro capture for workflow: {retro.workflow_id}")

if __name__ == "__main__":
    main()