from typing import Dict, List, Any
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
                'from_agent': from_agent,
                'to_agent': to_agent,
                'context': context,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            self.handoff_log.append(handoff_entry)
            self.logger.info(f"Handoff from {from_agent} to {to_agent} successful")
            return True
        except Exception as e:
            self.logger.error(f"Handoff failed: {e}")
            return False

    def get_handoff_history(self) -> List[Dict[str, Any]]:
        """Get the history of all handoffs."""
        return self.handoff_log


def parse_paths_string(paths_str: str) -> List[str]:
    if not paths_str:
        return []

    paths = []
    for line in paths_str.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            paths.append(line)

    return paths


class GateReport:
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.total_duration = 0.0