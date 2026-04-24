from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime

class AgentHandoffGate:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.handoff_log = []
    
    def process_handoff(self, from_agent: str, to_agent: str, context: Dict[str, Any]) -> bool:
        """Process an agent handoff with validation."""
        try:
            handoff_entry = {
                'timestamp': datetime.now().isoformat(),
                'from_agent': from_agent,
                'to_agent': to_agent,
                'context': context,
                'status': 'success'
            }
            self.handoff_log.append(handoff_entry)
            self.logger.info(f"Handoff successful: {from_agent} -> {to_agent}")
            return True
        except Exception as e:
            self.logger.error(f"Handoff failed: {e}")
            return False
    
    def get_handoff_history(self) -> List[Dict[str, Any]]:
        """Get the history of all handoffs."""
        return self.handoff_log

def parse_changed_paths(paths_str: str) -> List[str]:
    """Parse changed paths from a string input."""
    if not paths_str:
        return []
    
    paths = []
    for line in paths_str.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            paths.append(line)
    
    return paths

class HandoffMetrics:
    def __init__(self):
        self.handoff_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_duration = 0.0
    
    def record_handoff(self, success: bool, duration: float):
        """Record a handoff attempt."""
        self.handoff_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.total_duration += duration
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        success_rate = (self.success_count / self.handoff_count) if self.handoff_count > 0 else 0
        avg_duration = (self.total_duration / self.handoff_count) if self.handoff_count > 0 else 0
        
        return dict(
            total_handoffs=self.handoff_count,
            success_count=self.success_count,
            failure_count=self.failure_count,
            success_rate=success_rate,
            avg_duration=avg_duration
        )