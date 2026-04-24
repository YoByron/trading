from typing import Dict, List, Any
from datetime import datetime

class RetroCapture:
    """Capture and analyze workflow execution data for retrospective analysis."""
    
    def __init__(self):
        self.captures: List[Dict[str, Any]] = []
        
    def capture_event(self, event_type: str, data: Dict[str, Any]):
        """Capture a workflow event with timestamp."""
        capture = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }
        self.captures.append(capture)
        
    def get_captures(self) -> List[Dict[str, Any]]:
        """Return all captured events."""
        return self.captures
        
    def clear_captures(self):
        """Clear all captured events."""
        self.captures.clear()

class WorkflowStep:
    def __init__(self, name: str, handler):
        self.name = name
        self.handler = handler
        
class AgentWorkflowToolkit:
    def __init__(self):
        self.steps: List[WorkflowStep] = []
        self.retro_capture = RetroCapture()
        
    def add_step(self, step: WorkflowStep):
        self.steps.append(step)
        
    def execute_workflow(self):
        for step in self.steps:
            self.retro_capture.capture_event('step_start', {'step_name': step.name})
            try:
                step.handler()
                self.retro_capture.capture_event('step_complete', {'step_name': step.name})
            except Exception as e:
                self.retro_capture.capture_event('step_error', {
                    'step_name': step.name,
                    'error': str(e)
                })
                raise