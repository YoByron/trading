#!/usr/bin/env python3
"""Agent workflow toolkit for managing complex trading workflows."""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


@dataclass
class WorkflowStep:
    name: str
    description: str
    required_inputs: List[str]
    outputs: List[str]
    dependencies: List[str] = None


@dataclass
class WorkflowResult:
    step_name: str
    success: bool
    outputs: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class RetroCapture:
    timestamp: datetime
    workflow_name: str
    step_results: List[WorkflowResult]
    overall_success: bool
    total_execution_time: float
    metadata: Dict[str, Any] = None


class WorkflowEngine:
    """Engine for executing trading workflows with proper dependency management."""
    
    def __init__(self):
        self.workflows = {}
        self.step_registry = {}
        self.retro_captures = []
    
    def register_step(self, step: WorkflowStep, executor_func):
        """Register a workflow step with its executor function."""
        self.step_registry[step.name] = {
            'step': step,
            'executor': executor_func
        }
    
    def create_workflow(self, name: str, steps: List[str]):
        """Create a workflow from registered steps."""
        workflow_steps = []
        for step_name in steps:
            if step_name not in self.step_registry:
                raise ValueError(f"Step '{step_name}' not registered")
            workflow_steps.append(self.step_registry[step_name]['step'])
        
        self.workflows[name] = workflow_steps
    
    def execute_workflow(self, workflow_name: str, inputs: Dict[str, Any]) -> RetroCapture:
        """Execute a workflow and capture results."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        start_time = datetime.now()
        step_results = []
        available_data = inputs.copy()
        overall_success = True
        
        for step in self.workflows[workflow_name]:
            step_start = datetime.now()
            
            try:
                # Check dependencies
                if step.dependencies:
                    for dep in step.dependencies:
                        if dep not in [r.step_name for r in step_results if r.success]:
                            raise RuntimeError(f"Dependency '{dep}' not satisfied")
                
                # Check required inputs
                for required_input in step.required_inputs:
                    if required_input not in available_data:
                        raise ValueError(f"Required input '{required_input}' not available")
                
                # Execute step
                executor = self.step_registry[step.name]['executor']
                result_data = executor(available_data)
                
                # Update available data
                if isinstance(result_data, dict):
                    available_data.update(result_data)
                
                step_duration = (datetime.now() - step_start).total_seconds()
                
                step_result = WorkflowResult(
                    step_name=step.name,
                    success=True,
                    outputs=result_data,
                    execution_time=step_duration
                )
                
            except Exception as e:
                step_duration = (datetime.now() - step_start).total_seconds()
                step_result = WorkflowResult(
                    step_name=step.name,
                    success=False,
                    outputs={},
                    error_message=str(e),
                    execution_time=step_duration
                )
                overall_success = False
            
            step_results.append(step_result)
            
            # Stop on failure if step is critical
            if not step_result.success:
                print(f"❌ Step '{step.name}' failed: {step_result.error_message}")
                break
            else:
                print(f"✅ Step '{step.name}' completed successfully")
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        retro_capture = RetroCapture(
            timestamp=start_time,
            workflow_name=workflow_name,
            step_results=step_results,
            overall_success=overall_success,
            total_execution_time=total_time
        )
        
        self.retro_captures.append(retro_capture)
        return retro_capture
    
    def get_workflow_history(self, workflow_name: Optional[str] = None) -> List[RetroCapture]:
        """Get execution history for workflows."""
        if workflow_name:
            return [rc for rc in self.retro_captures if rc.workflow_name == workflow_name]
        return self.retro_captures.copy()


def create_sample_workflow():
    """Create a sample trading workflow for demonstration."""
    engine = WorkflowEngine()
    
    # Register sample steps
    def market_data_step(inputs):
        return {"market_data": "sample_data", "timestamp": datetime.now().isoformat()}
    
    def analysis_step(inputs):
        return {"analysis_result": "bullish", "confidence": 0.85}
    
    def signal_generation_step(inputs):
        return {"signal": "BUY", "quantity": 100}
    
    # Define steps
    market_data = WorkflowStep(
        name="market_data",
        description="Fetch market data",
        required_inputs=[],
        outputs=["market_data", "timestamp"]
    )
    
    analysis = WorkflowStep(
        name="analysis",
        description="Analyze market data",
        required_inputs=["market_data"],
        outputs=["analysis_result", "confidence"],
        dependencies=["market_data"]
    )
    
    signal_gen = WorkflowStep(
        name="signal_generation",
        description="Generate trading signal",
        required_inputs=["analysis_result"],
        outputs=["signal", "quantity"],
        dependencies=["analysis"]
    )
    
    # Register steps
    engine.register_step(market_data, market_data_step)
    engine.register_step(analysis, analysis_step)
    engine.register_step(signal_gen, signal_generation_step)
    
    # Create workflow
    engine.create_workflow("sample_trading", ["market_data", "analysis", "signal_generation"])
    
    return engine


if __name__ == "__main__":
    engine = create_sample_workflow()
    result = engine.execute_workflow("sample_trading", {})
    
    print(f"\n📊 Workflow Result:")
    print(f"Success: {result.overall_success}")
    print(f"Total Time: {result.total_execution_time:.2f}s")
    print(f"Steps Executed: {len(result.step_results)}")