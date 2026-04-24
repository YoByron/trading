import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

def build_retro_markdown(workflow_data: Dict[str, Any]) -> str:
    """Build a retrospective markdown report from workflow data."""
    lines = ["# Workflow Retrospective", ""]
    
    # Add timestamp
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append("")
    
    # Add workflow summary
    if "summary" in workflow_data:
        lines.append("## Summary")
        lines.append(workflow_data["summary"])
        lines.append("")
    
    # Add steps if available
    if "steps" in workflow_data:
        lines.append("## Steps Executed")
        for i, step in enumerate(workflow_data["steps"], 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    
    # Add results if available
    if "results" in workflow_data:
        lines.append("## Results")
        lines.append(str(workflow_data["results"]))
        lines.append("")
    
    # Add lessons learned
    if "lessons" in workflow_data:
        lines.append("## Lessons Learned")
        for lesson in workflow_data["lessons"]:
            lines.append(f"- {lesson}")
        lines.append("")
    
    return "\n".join(lines)

def analyze_workflow_performance(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze workflow performance metrics."""
    analysis = {
        "total_steps": len(workflow_data.get("steps", [])),
        "success_rate": workflow_data.get("success_rate", 0.0),
        "duration": workflow_data.get("duration", 0),
        "recommendations": []
    }
    
    # Add recommendations based on performance
    if analysis["success_rate"] < 0.8:
        analysis["recommendations"].append("Consider reviewing failed steps")
    
    if analysis["duration"] > 300:  # 5 minutes
        analysis["recommendations"].append("Workflow may benefit from optimization")
    
    return analysis