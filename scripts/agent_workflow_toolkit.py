from typing import Dict, List, Any, Optional, NamedTuple
import json
import os
from datetime import datetime

class RetroCapture(NamedTuple):
    """Capture of workflow execution for retrospective analysis."""
    timestamp: str
    workflow_id: str
    step_results: List[Dict[str, Any]]
    final_outcome: str
    metrics: Dict[str, Any]

def capture_workflow_execution(
    workflow_id: str,
    step_results: List[Dict[str, Any]],
    final_outcome: str,
    metrics: Optional[Dict[str, Any]] = None
) -> RetroCapture:
    """Capture workflow execution for analysis.
    
    Args:
        workflow_id: Unique identifier for the workflow
        step_results: Results from each step in the workflow
        final_outcome: Final result of the workflow
        metrics: Optional metrics about the execution
        
    Returns:
        RetroCapture object with execution data
    """
    return RetroCapture(
        timestamp=datetime.now().isoformat(),
        workflow_id=workflow_id,
        step_results=step_results,
        final_outcome=final_outcome,
        metrics=metrics or {}
    )

def save_retro_capture(capture: RetroCapture, output_dir: str = "workflow_captures") -> str:
    """Save a RetroCapture to disk.
    
    Args:
        capture: RetroCapture object to save
        output_dir: Directory to save the capture file
        
    Returns:
        Path to the saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{capture.workflow_id}_{capture.timestamp.replace(':', '-')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(capture._asdict(), f, indent=2)
    
    return filepath

def load_retro_capture(filepath: str) -> RetroCapture:
    """Load a RetroCapture from disk.
    
    Args:
        filepath: Path to the capture file
        
    Returns:
        RetroCapture object
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return RetroCapture(**data)

def analyze_workflow_patterns(captures_dir: str = "workflow_captures") -> Dict[str, Any]:
    """Analyze patterns across multiple workflow captures.
    
    Args:
        captures_dir: Directory containing capture files
        
    Returns:
        Analysis results
    """
    if not os.path.exists(captures_dir):
        return {"error": "Captures directory not found"}
    
    captures = []
    for filename in os.listdir(captures_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(captures_dir, filename)
            try:
                captures.append(load_retro_capture(filepath))
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
    
    if not captures:
        return {"error": "No valid captures found"}
    
    # Basic analysis
    analysis = {
        "total_workflows": len(captures),
        "unique_workflow_ids": len(set(c.workflow_id for c in captures)),
        "outcomes": {},
        "avg_steps": 0,
        "common_metrics": {}
    }
    
    # Analyze outcomes
    for capture in captures:
        outcome = capture.final_outcome
        analysis["outcomes"][outcome] = analysis["outcomes"].get(outcome, 0) + 1
    
    # Average steps
    total_steps = sum(len(c.step_results) for c in captures)
    analysis["avg_steps"] = total_steps / len(captures) if captures else 0
    
    return analysis

def main():
    """Example usage of the workflow toolkit."""
    # Example workflow execution
    step_results = [
        {"step": "initialize", "status": "success", "duration": 1.2},
        {"step": "process_data", "status": "success", "duration": 3.5},
        {"step": "generate_output", "status": "success", "duration": 0.8}
    ]
    
    metrics = {
        "total_duration": 5.5,
        "memory_usage": "45MB",
        "cpu_utilization": "12%"
    }
    
    capture = capture_workflow_execution(
        workflow_id="example_workflow_001",
        step_results=step_results,
        final_outcome="success",
        metrics=metrics
    )
    
    saved_path = save_retro_capture(capture)
    print(f"Workflow capture saved to: {saved_path}")
    
    # Analyze patterns
    analysis = analyze_workflow_patterns()
    print(f"Workflow analysis: {json.dumps(analysis, indent=2)}")

if __name__ == "__main__":
    main()