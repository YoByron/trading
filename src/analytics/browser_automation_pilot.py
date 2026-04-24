import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BrowserPilotRunResult:
    success: bool
    execution_time: float
    steps_completed: int
    total_steps: int
    error_message: str = ""
    screenshots: List[str] = None
    data_extracted: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []
        if self.data_extracted is None:
            self.data_extracted = {}

class BrowserAutomationStep:
    def __init__(self, action: str, target: str, value: str = ""):
        self.action = action
        self.target = target
        self.value = value
        self.completed = False
        self.error_message = ""

class BrowserAutomationPilot:
    def __init__(self):
        self.steps: List[BrowserAutomationStep] = []
        self.current_step = 0
        self.is_running = False

    def add_step(self, action: str, target: str, value: str = ""):
        step = BrowserAutomationStep(action, target, value)
        self.steps.append(step)

    def execute_automation(self) -> BrowserPilotRunResult:
        start_time = datetime.now()
        self.is_running = True
        
        completed_steps = 0
        error_message = ""
        
        try:
            for i, step in enumerate(self.steps):
                self.current_step = i
                success = self._execute_step(step)
                
                if success:
                    step.completed = True
                    completed_steps += 1
                else:
                    error_message = step.error_message
                    break
            
            execution_time = (datetime.now() - start_time).total_seconds()
            success = completed_steps == len(self.steps)
            
            return BrowserPilotRunResult(
                success=success,
                execution_time=execution_time,
                steps_completed=completed_steps,
                total_steps=len(self.steps),
                error_message=error_message
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return BrowserPilotRunResult(
                success=False,
                execution_time=execution_time,
                steps_completed=completed_steps,
                total_steps=len(self.steps),
                error_message=str(e)
            )
        finally:
            self.is_running = False

    def _execute_step(self, step: BrowserAutomationStep) -> bool:
        try:
            # Simulate step execution
            return True
        except Exception as e:
            step.error_message = str(e)
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "current_step": self.current_step,
            "total_steps": len(self.steps),
            "completed_steps": sum(1 for step in self.steps if step.completed)
        }