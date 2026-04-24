#!/usr/bin/env python3

import json
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class WorkflowStep:
    step_id: str
    status: str
    duration: float
    timestamp: datetime

@dataclass
class WorkflowAnalysis:
    workflow_id: str
    steps: List[WorkflowStep]
    success_rate: float
    total_duration: float
    recommendations: List[str]

@dataclass
class RetroCapture:
    workflow_id: str
    analysis: WorkflowAnalysis
    markdown_report: str
    timestamp: datetime

def analyze_workflow_performance(workflow_data: Dict[str, Any]) -> WorkflowAnalysis:
    """Analyze workflow performance and generate insights."""
    steps = []
    for step_data in workflow_data.get("steps", []):
        steps.append(WorkflowStep(
            step_id=step_data["id"],
            status=step_data["status"],
            duration=step_data.get("duration", 0),
            timestamp=datetime.fromisoformat(step_data["timestamp"])
        ))

    completed_steps = [s for s in steps if s.status == "completed"]
    success_rate = len(completed_steps) / len(steps) if steps else 0

    return WorkflowAnalysis(
        workflow_id=workflow_data["id"],
        steps=steps,
        success_rate=success_rate,
        total_duration=sum(s.duration for s in steps),
        recommendations=generate_recommendations(steps)
    )

def build_retro_markdown(analysis: WorkflowAnalysis) -> str:
    markdown = f"# Workflow Retrospective: {analysis.workflow_id}\n\n"
    markdown += "## Summary\n"
    markdown += f"- Success Rate: {analysis.success_rate:.2%}\n"
    markdown += f"- Total Duration: {analysis.total_duration:.2f}s\n"
    markdown += f"- Total Steps: {len(analysis.steps)}\n\n"

    markdown += "## Recommendations\n"
    for rec in analysis.recommendations:
        markdown += f"- {rec}\n"
    
    return markdown

def generate_recommendations(steps: List[WorkflowStep]) -> List[str]:
    """Generate recommendations based on workflow analysis."""
    recommendations = []
    
    failed_steps = [s for s in steps if s.status == "failed"]
    if failed_steps:
        recommendations.append(f"Investigate {len(failed_steps)} failed steps")
    
    slow_steps = [s for s in steps if s.duration > 30]
    if slow_steps:
        recommendations.append(f"Optimize {len(slow_steps)} slow-running steps")
    
    if not recommendations:
        recommendations.append("Workflow performing well - no immediate recommendations")
    
    return recommendations

def capture_retrospective(workflow_data: Dict[str, Any]) -> RetroCapture:
    """Capture a complete retrospective analysis."""
    analysis = analyze_workflow_performance(workflow_data)
    markdown_report = build_retro_markdown(analysis)
    
    return RetroCapture(
        workflow_id=workflow_data["id"],
        analysis=analysis,
        markdown_report=markdown_report,
        timestamp=datetime.now()
    )

def main():
    # Example workflow data
    sample_workflow = {
        "id": "workflow-123",
        "steps": [
            {
                "id": "step-1",
                "status": "completed",
                "duration": 15.5,
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "id": "step-2", 
                "status": "failed",
                "duration": 5.2,
                "timestamp": "2024-01-01T10:00:15"
            }
        ]
    }
    
    retro = capture_retrospective(sample_workflow)
    print(retro.markdown_report)

if __name__ == "__main__":
    main()