from typing import Dict, Any
from dataclasses import dataclass
import datetime

@dataclass
class ContextBundle:
    context_id: str
    agent_id: str
    workflow_step: str
    context_data: Dict[str, Any]
    timestamp: str

@dataclass
class WorkflowStep:
    step_id: str
    step_name: str
    agent_id: str
    input_context: Dict[str, Any]
    output_context: Dict[str, Any]
    status: str
    timestamp: str

class AgentWorkflowToolkit:
    def __init__(self):
        self.steps = []

    def add_step(self, step: WorkflowStep):
        self.steps.append(step)

    def get_context(self, step_id: str) -> Dict[str, Any]:
        for step in self.steps:
            if step.step_id == step_id:
                return step.output_context
        return {}

def build_context_bundle(context_id: str, agent_id: str, workflow_step: str, data: Dict[str, Any]) -> ContextBundle:
    return ContextBundle(
        context_id=context_id,
        agent_id=agent_id,
        workflow_step=workflow_step,
        context_data=data,
        timestamp=datetime.datetime.now().isoformat(),
        data=data
    )