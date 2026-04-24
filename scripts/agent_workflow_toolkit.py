"""Agent workflow toolkit for retrospective analysis"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

@dataclass
class RetroCapture:
    """Capture workflow data for retrospective analysis"""
    timestamp: str
    workflow_id: str
    event_type: str
    details: Dict

@dataclass
class ContextBundle:
    """Bundle of context information"""
    workflow_captures: List[RetroCapture]
    metadata: Dict
    bundle_id: str

def capture_workflow_event(workflow_id: str, event_type: str, details: Dict) -> RetroCapture:
    """Capture a workflow event for retrospective analysis"""
    import datetime

    return RetroCapture(
        timestamp=datetime.datetime.now().isoformat(),
        workflow_id=workflow_id,
        event_type=event_type,
        details=details
    )

def save_retro_capture(capture: RetroCapture, output_file: str):
    """Save retrospective capture to file"""
    capture_data = {
        'timestamp': capture.timestamp,
        'event_type': capture.event_type,
        'details': capture.details,
        'workflow_id': capture.workflow_id
    }

    with open(output_file, 'w') as f:
        json.dump(capture_data, f, indent=2)

def load_retro_captures(input_file: str) -> List[RetroCapture]:
    """Load retrospective captures from file"""
    if not Path(input_file).exists():
        return []

    with open(input_file, 'r') as f:
        data = json.load(f)

    if isinstance(data, dict):
        return [RetroCapture(
            timestamp=data.get('timestamp', ''),
            event_type=data.get('event_type', ''),
            details=data.get('details', {}),
            workflow_id=data.get('workflow_id', '')
        )]
    elif isinstance(data, list):
        return [RetroCapture(
            timestamp=item.get('timestamp', ''),
            event_type=item.get('event_type', ''),
            details=item.get('details', {}),
            workflow_id=item.get('workflow_id', '')
        ) for item in data]

    return []

def build_context_bundle(captures: List[RetroCapture], bundle_id: str) -> ContextBundle:
    """Build context bundle from captures"""
    metadata = {
        "capture_count": len(captures),
        "workflows": list(set(c.workflow_id for c in captures)),
        "event_types": list(set(c.event_type for c in captures))
    }
    
    return ContextBundle(
        workflow_captures=captures,
        metadata=metadata,
        bundle_id=bundle_id
    )