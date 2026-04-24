from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime

@dataclass
class WorkflowStep:
    name: str
    status: str
    timestamp: datetime
    details: Dict[str, Any]

@dataclass
class RetroCapture:
    workflow_id: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any]
    created_at: datetime

def capture_workflow_execution(workflow_id: str, steps: List[Dict]) -> RetroCapture:
    """Capture workflow execution for retrospective analysis"""
    workflow_steps = [
        WorkflowStep(
            name=step.get('name', 'Unknown'),
            status=step.get('status', 'pending'),
            timestamp=datetime.now(),
            details=step.get('details', {})
        )
        for step in steps
    ]
    
    return RetroCapture(
        workflow_id=workflow_id,
        steps=workflow_steps,
        metadata={'total_steps': len(workflow_steps)},
        created_at=datetime.now()
    )

def analyze_workflow_performance(retro: RetroCapture) -> Dict[str, Any]:
    """Analyze workflow performance metrics"""
    successful_steps = sum(1 for step in retro.steps if step.status == 'completed')
    failed_steps = sum(1 for step in retro.steps if step.status == 'failed')
    
    return {
        'total_steps': len(retro.steps),
        'successful_steps': successful_steps,
        'failed_steps': failed_steps,
        'success_rate': successful_steps / len(retro.steps) if retro.steps else 0
    }