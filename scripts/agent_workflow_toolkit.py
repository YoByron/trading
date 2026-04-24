import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    status: str
    result: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


@dataclass
class WorkflowAnalysis:
    workflow_id: str
    steps: List[WorkflowStep]
    success_rate: float
    total_duration: float


def analyze_workflow_performance(workflow_data: Dict[str, Any]) -> WorkflowAnalysis:
    steps = []
    for step_data in workflow_data.get("steps", []):
        steps.append(WorkflowStep(
            step_id=step_data["id"],
            name=step_data["name"],
            status=step_data["status"],
            result=step_data.get("result"),
            timestamp=datetime.fromisoformat(step_data["timestamp"])
        ))
    
    completed_steps = [s for s in steps if s.status == "completed"]
    success_rate = len(completed_steps) / len(steps) if steps else 0
    
    return WorkflowAnalysis(
        workflow_id=workflow_data["id"],
        steps=steps,
        success_rate=success_rate,
        total_duration=workflow_data.get("duration", 0)
    )


def build_retro_markdown(analysis: WorkflowAnalysis) -> str:
    markdown = f"# Workflow Retrospective: {analysis.workflow_id}\n\n"
    markdown += f"## Summary\n"
    markdown += f"- Success Rate: {analysis.success_rate:.2%}\n"
    markdown += f"- Total Duration: {analysis.total_duration:.2f}s\n"
    markdown += f"- Total Steps: {len(analysis.steps)}\n\n"
    
    markdown += "## Step Details\n"
    for step in analysis.steps:
        status_emoji = "✅" if step.status == "completed" else "❌"
        markdown += f"- {status_emoji} **{step.name}** ({step.step_id})\n"
        if step.result:
            markdown += f"  - Result: {json.dumps(step.result, indent=2)}\n"
    
    return markdown


def optimize_workflow_sequence(steps: List[WorkflowStep]) -> List[str]:
    completed_first = [s for s in steps if s.status == "completed"]
    failed_last = [s for s in steps if s.status != "completed"]
    
    optimized = [s.step_id for s in completed_first] + [s.step_id for s in failed_last]
    return optimized


def main():
    sample_data = {
        "id": "workflow_001",
        "duration": 45.5,
        "steps": [
            {
                "id": "step1",
                "name": "Data Collection",
                "status": "completed",
                "result": {"records": 100},
                "timestamp": "2023-01-01T10:00:00"
            },
            {
                "id": "step2", 
                "name": "Analysis",
                "status": "failed",
                "timestamp": "2023-01-01T10:05:00"
            }
        ]
    }
    
    analysis = analyze_workflow_performance(sample_data)
    markdown = build_retro_markdown(analysis)
    print(markdown)


if __name__ == "__main__":
    main()