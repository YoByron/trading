from typing import Dict, List, Any

class WorkflowStep:
    def __init__(self, name: str, action: str):
        self.name = name
        self.action = action
        self.completed = False

class ContextBundle:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

def build_context_bundle(data: Dict[str, Any] = None) -> ContextBundle:
    bundle = ContextBundle()
    if data:
        bundle.data = data
    return bundle

class AgentWorkflowToolkit:
    def __init__(self):
        self.steps: List[WorkflowStep] = []
        
    def add_step(self, step: WorkflowStep):
        self.steps.append(step)
        
    def execute_workflow(self) -> bool:
        for step in self.steps:
            if self._execute_step(step.__dict__):
                step.completed = True
            else:
                return False
        return True
        
    def _execute_step(self, step: Dict[str, Any]) -> bool:
        return True