import sys
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
import json

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

@dataclass
class RetroCapture:
    timestamp: str
    event_type: str
    data: Dict[str, Any]
    workflow_id: str = ""

def capture_workflow_event(event_type: str, data: Dict[str, Any]) -> RetroCapture:
    """Capture a workflow event for retrospective analysis"""
    import datetime
    
    return RetroCapture(
        timestamp=datetime.datetime.now().isoformat(),
        event_type=event_type,
        data=data
    )

def save_retro_capture(capture: RetroCapture, output_file: str = "workflow_retro.json"):
    """Save retrospective capture to file"""
    capture_data = {
        'timestamp': capture.timestamp,
        'event_type': capture.event_type,
        'data': capture.data,
        'workflow_id': capture.workflow_id
    }
    
    with open(output_file, 'w') as f:
        json.dump(capture_data, f, indent=2)

def load_retro_captures(input_file: str = "workflow_retro.json") -> List[RetroCapture]:
    """Load retrospective captures from file"""
    if not Path(input_file).exists():
        return []
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        return [RetroCapture(
            timestamp=data['timestamp'],
            event_type=data['event_type'],
            data=data['data'],
            workflow_id=data.get('workflow_id', '')
        )]
    elif isinstance(data, list):
        return [RetroCapture(
            timestamp=item['timestamp'],
            event_type=item['event_type'],
            data=item['data'],
            workflow_id=item.get('workflow_id', '')
        ) for item in data]
    
    return []

def main():
    """Main entry point for workflow toolkit"""
    print("Agent Workflow Toolkit initialized")
    return 0

if __name__ == "__main__":
    sys.exit(main())