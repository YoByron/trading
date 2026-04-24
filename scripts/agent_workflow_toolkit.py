from dataclasses import dataclass
from typing import Dict, List, Any
from datetime import datetime


@dataclass
class WorkflowStep:
    step_id: str
    status: str
    timestamp: datetime
    details: Dict[str, Any]


@dataclass
class RetroCapture:
    workflow_id: str
    timestamp: datetime
    steps: List[WorkflowStep]
    metadata: Dict[str, Any]


def build_context_bundle(workflow_id: str, steps: List[Dict[str, Any]]) -> RetroCapture:
    """Build a context bundle from workflow steps."""
    workflow_steps = [
        WorkflowStep(
            step_id=step.get('id', ''),
            status=step.get('status', 'unknown'),
            timestamp=datetime.fromisoformat(step.get('timestamp', datetime.now().isoformat())),
            details=step.get('details', {})
        )
        for step in steps
    ]

    return RetroCapture(
        workflow_id=workflow_id,
        timestamp=datetime.now(),
        steps=workflow_steps,
        metadata={}
    )


def analyze_workflow_performance(retro: RetroCapture) -> Dict[str, Any]:
    """Analyze workflow performance from retro capture."""
    successful_steps = sum(1 for step in retro.steps if step.status == 'completed')
    failed_steps = sum(1 for step in retro.steps if step.status == 'failed')

    return {
        'total_steps': len(retro.steps),
        'successful_steps': successful_steps,
        'failed_steps': failed_steps,
        'success_rate': successful_steps / len(retro.steps) if retro.steps else 0,
        'workflow_duration': (retro.steps[-1].timestamp - retro.steps[0].timestamp).total_seconds() if retro.steps else 0
    }