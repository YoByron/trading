import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

def build_retro_markdown(workflow_data: Dict[str, Any]) -> str:
    """Build retrospective markdown report from workflow data"""

    # Extract key metrics
    start_time = workflow_data.get('start_time', 'Unknown')
    end_time = workflow_data.get('end_time', 'Unknown')
    duration = workflow_data.get('duration', 'Unknown')
    status = workflow_data.get('status', 'Unknown')
    steps = workflow_data.get('steps', [])

    # Build markdown report
    markdown = f"""# Workflow Retrospective

## Summary
- **Start Time**: {start_time}
- **End Time**: {end_time}
- **Duration**: {duration}
- **Status**: {status}
- **Steps Completed**: {len(steps)}

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

    return markdown

class RetroCapture:
    """Capture and process workflow retrospectives"""
    
    def __init__(self, output_dir: str = "retrospectives"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def capture_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Capture workflow data for retrospective analysis"""
        timestamp = datetime.now().isoformat()
        
        # Save raw data
        raw_file = self.output_dir / f"{workflow_id}_{timestamp}_raw.json"
        with open(raw_file, 'w') as f:
            json.dump(workflow_data, f, indent=2)
        
        # Generate markdown report
        markdown = build_retro_markdown(workflow_data)
        md_file = self.output_dir / f"{workflow_id}_{timestamp}_report.md"
        with open(md_file, 'w') as f:
            f.write(markdown)
        
        return {
            'raw_file': str(raw_file),
            'report_file': str(md_file),
            'timestamp': timestamp
        }

def main():
    """Main function for workflow toolkit"""
    retro = RetroCapture()
    
    # Example workflow data
    sample_workflow = {
        'start_time': '2024-01-01T10:00:00',
        'end_time': '2024-01-01T10:30:00',
        'duration': '30m',
        'status': 'completed',
        'steps': [
            {'name': 'Initialize', 'status': 'completed', 'duration': '5m'},
            {'name': 'Process Data', 'status': 'completed', 'duration': '20m'},
            {'name': 'Generate Report', 'status': 'completed', 'duration': '5m'}
        ]
    }
    
    result = retro.capture_workflow('sample_workflow', sample_workflow)
    print(f"Generated retrospective: {result}")

if __name__ == "__main__":
    main()