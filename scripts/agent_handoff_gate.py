#!/usr/bin/env python3

import json
import sys
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class HandoffStep:
    def __init__(self, step_id: str, description: str, status: StepStatus = StepStatus.PENDING):
        self.step_id = step_id
        self.description = description
        self.status = status
        self.metadata: Dict[str, Any] = {}

class AgentHandoffGate:
    def __init__(self):
        self.steps: List[HandoffStep] = []
        self.current_step_index = 0
    
    def add_step(self, step: HandoffStep):
        self.steps.append(step)
    
    def execute_current_step(self) -> bool:
        if self.current_step_index >= len(self.steps):
            return True
        
        current_step = self.steps[self.current_step_index]
        current_step.status = StepStatus.RUNNING
        
        try:
            success = self._execute_step_logic(current_step)
            if success:
                current_step.status = StepStatus.COMPLETED
                self.current_step_index += 1
                return True
            else:
                current_step.status = StepStatus.FAILED
                return False
        except Exception as e:
            current_step.status = StepStatus.FAILED
            current_step.metadata["error"] = str(e)
            return False
    
    def _execute_step_logic(self, step: HandoffStep) -> bool:
        print(f"Executing step: {step.description}")
        return True
    
    def get_progress_report(self) -> Dict[str, Any]:
        completed_steps = [s for s in self.steps if s.status == StepStatus.COMPLETED]
        return {
            "total_steps": len(self.steps),
            "completed_steps": len(completed_steps),
            "current_step": self.current_step_index,
            "progress_percentage": len(completed_steps) / len(self.steps) * 100 if self.steps else 0
        }

def parse_changed_paths(git_output: str) -> List[str]:
    """Parse git diff output to extract changed file paths."""
    lines = git_output.strip().split('\n')
    paths = []
    for line in lines:
        if line and not line.startswith('diff --git'):
            # Simple parsing - extract file paths from git diff output
            if line.startswith('+++') or line.startswith('---'):
                path = line[4:].strip()
                if path != '/dev/null' and path not in paths:
                    paths.append(path)
    return paths

def create_handoff_context(changed_files: List[str]) -> Dict[str, Any]:
    """Create context for agent handoff based on changed files."""
    context = {
        "changed_files": changed_files,
        "file_types": {},
        "affected_modules": []
    }
    
    for file_path in changed_files:
        path_obj = Path(file_path)
        ext = path_obj.suffix.lower()
        context["file_types"][ext] = context["file_types"].get(ext, 0) + 1
        
        # Determine affected modules
        if 'src/' in file_path:
            context["affected_modules"].append("core")
        elif 'tests/' in file_path:
            context["affected_modules"].append("testing")
        elif 'scripts/' in file_path:
            context["affected_modules"].append("scripts")
    
    return context

def main():
    gate = AgentHandoffGate()
    
    # Add sample handoff steps
    gate.add_step(HandoffStep("validate", "Validate code changes"))
    gate.add_step(HandoffStep("test", "Run test suite"))
    gate.add_step(HandoffStep("deploy", "Deploy to staging"))
    
    # Execute all steps
    while gate.current_step_index < len(gate.steps):
        success = gate.execute_current_step()
        if not success:
            print("Step failed!")
            break
    
    # Print final report
    report = gate.get_progress_report()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()