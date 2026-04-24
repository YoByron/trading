from typing import List, Dict, Any, Callable
from datetime import datetime

class RetroCapture:
    """Capture and analyze workflow execution data for retrospective analysis."""

    def __init__(self):
        self.captures: List[Dict[str, Any]] = []

    def capture_event(self, event_type: str, data: Dict[str, Any]):
        """Capture a workflow event with timestamp."""
        capture = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.captures.append(capture)

    def get_captures(self) -> List[Dict[str, Any]]:
        """Return all captured events."""
        return self.captures

    def clear_captures(self):
        """Clear all captured events."""
        self.captures.clear()

class WorkflowStep:
    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler

class AgentWorkflowToolkit:
    def __init__(self):
        self.steps: List[WorkflowStep] = []
        self.retro_capture = RetroCapture()

    def add_step(self, name: str, handler: Callable):
        """Add a workflow step."""
        step = WorkflowStep(name, handler)
        self.steps.append(step)

    def execute_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow steps."""
        self.retro_capture.capture_event("workflow_start", {"context": context})
        
        result = context.copy()
        for step in self.steps:
            try:
                step_result = step.handler(result)
                result.update(step_result or {})
                self.retro_capture.capture_event("step_complete", {
                    "step_name": step.name,
                    "result": step_result
                })
            except Exception as e:
                self.retro_capture.capture_event("step_error", {
                    "step_name": step.name,
                    "error": str(e)
                })
                raise
        
        self.retro_capture.capture_event("workflow_complete", {"final_result": result})
        return result

def build_context_bundle(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a context bundle for workflow execution."""
    return {
        "timestamp": datetime.now().isoformat(),
        "data": data,
        "metadata": {
            "created_by": "workflow_toolkit",
            "version": "1.0"
        }
    }

def analyze_workflow_performance(toolkit: AgentWorkflowToolkit) -> Dict[str, Any]:
    """Analyze workflow performance from captured events."""
    captures = toolkit.retro_capture.get_captures()
    
    if not captures:
        return {"total_events": 0, "analysis": "No data available"}
    
    step_times = {}
    errors = []
    
    for capture in captures:
        if capture["event_type"] == "step_complete":
            step_name = capture["data"]["step_name"]
            step_times[step_name] = step_times.get(step_name, 0) + 1
        elif capture["event_type"] == "step_error":
            errors.append(capture["data"])
    
    return {
        "total_events": len(captures),
        "step_execution_counts": step_times,
        "error_count": len(errors),
        "errors": errors
    }