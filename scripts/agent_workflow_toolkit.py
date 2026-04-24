"""Agent workflow toolkit for coordination and reporting"""
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

def build_retro_markdown(workflow_data: Dict[str, Any]) -> str:
    """Build retrospective markdown report from workflow data"""
    
    # Extract key metrics
    start_time = workflow_data.get('start_time', 'Unknown')
    end_time = workflow_data.get('end_time', 'Unknown')
    status = workflow_data.get('status', 'Unknown')
    steps = workflow_data.get('steps', [])
    
    # Build markdown report
    markdown = f"""# Workflow Retrospective

## Summary
- **Start Time**: {start_time}
- **End Time**: {end_time}
- **Status**: {status}
- **Total Steps**: {len(steps)}

## Execution Steps
"""
    
    for i, step in enumerate(steps, 1):
        step_name = step.get('name', f'Step {i}')
        step_status = step.get('status', 'Unknown')
        step_duration = step.get('duration', 'Unknown')
        
        markdown += f"""
### {i}. {step_name}
- **Status**: {step_status}
- **Duration**: {step_duration}
"""
        
        if 'error' in step:
            markdown += f"- **Error**: {step['error']}\n"
        
        if 'output' in step:
            markdown += f"- **Output**: {step['output']}\n"
    
    # Add recommendations if any failures
    failed_steps = [s for s in steps if s.get('status') == 'failed']
    if failed_steps:
        markdown += "\n## Recommendations\n"
        for step in failed_steps:
            markdown += f"- Review and fix: {step.get('name', 'Unknown step')}\n"
    
    return markdown

def coordinate_agent_handoff(from_agent: str, to_agent: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Coordinate handoff between agents"""
    
    handoff_data = {
        'timestamp': datetime.now().isoformat(),
        'from_agent': from_agent,
        'to_agent': to_agent,
        'context': context,
        'status': 'initiated'
    }
    
    # Validate context data
    required_keys = ['task_id', 'current_state']
    missing_keys = [key for key in required_keys if key not in context]
    
    if missing_keys:
        handoff_data['status'] = 'failed'
        handoff_data['error'] = f"Missing required context keys: {missing_keys}"
    else:
        handoff_data['status'] = 'completed'
    
    return handoff_data

if __name__ == "__main__":
    # Example usage
    sample_workflow = {
        'start_time': '2023-01-01T10:00:00',
        'end_time': '2023-01-01T11:30:00',
        'status': 'completed',
        'steps': [
            {
                'name': 'Data Collection',
                'status': 'completed',
                'duration': '30 minutes'
            },
            {
                'name': 'Analysis',
                'status': 'failed',
                'duration': '45 minutes',
                'error': 'Connection timeout'
            }
        ]
    }
    
    markdown_report = build_retro_markdown(sample_workflow)
    print(markdown_report)