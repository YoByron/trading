import datetime
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class RetroCapture:
    """Captures retrospective information for workflow analysis."""
    agent_id: str
    workflow_step: str
    timestamp: str
    performance_metrics: Dict[str, Any]
    context: Dict[str, Any]

@dataclass
class WorkflowState:
    """Represents current state of workflow execution."""
    workflow_id: str
    current_step: str
    completed_steps: list
    data: Dict[str, Any]

def create_retro_capture(agent_id: str, workflow_step: str,
                        performance_metrics: Dict[str, Any] = None,
                        context: Dict[str, Any] = None) -> RetroCapture:
    """Create a retrospective capture for workflow analysis."""
    return RetroCapture(
        agent_id=agent_id,
        workflow_step=workflow_step,
        timestamp=datetime.datetime.now().isoformat(),
        performance_metrics=performance_metrics or {},
        context=context or {}
    )

def build_retro_markdown(retro_capture: RetroCapture) -> str:
    """Build markdown report from retrospective capture."""
    return f"""# Workflow Retrospective

## Agent: {retro_capture.agent_id}
## Step: {retro_capture.workflow_step}
## Timestamp: {retro_capture.timestamp}

### Performance Metrics
{retro_capture.performance_metrics}

### Context
{retro_capture.context}
"""