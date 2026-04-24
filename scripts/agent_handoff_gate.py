from typing import List, Dict, Any, Optional
from datetime import datetime

class HandoffContext:
    """Context for agent handoffs with metadata and state tracking."""

    def __init__(self, source_agent: str, target_agent: str):
        self.source_agent = source_agent
        self.target_agent = target_agent
        self.timestamp = datetime.now()
        self.handoff_id = f"{source_agent}->{target_agent}-{self.timestamp.isoformat()}"
        self.metadata: Dict[str, Any] = {}
        self.state_data: Dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the handoff context."""
        self.metadata[key] = value

    def set_state(self, state: Dict[str, Any]):
        """Set the state data for handoff."""
        self.state_data = state

class GateReport:
    """Report for handoff gate analysis."""
    
    def __init__(self, handoff_count: int, success_rate: float, avg_duration: float):
        self.handoff_count = handoff_count
        self.success_rate = success_rate
        self.avg_duration = avg_duration
        self.timestamp = datetime.now()

class AgentHandoffGate:
    """Gate for managing agent handoffs and transitions."""

    def __init__(self):
        self.handoffs: List[HandoffContext] = []
        self.active_handoffs: Dict[str, HandoffContext] = {}

    def initiate_handoff(self, source_agent: str, target_agent: str,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Initiate a handoff between agents."""
        context = HandoffContext(source_agent, target_agent)
        if metadata:
            for key, value in metadata.items():
                context.add_metadata(key, value)

        self.handoffs.append(context)
        self.active_handoffs[context.handoff_id] = context
        return context.handoff_id

    def complete_handoff(self, handoff_id: str, success: bool = True) -> bool:
        """Complete a handoff."""
        if handoff_id in self.active_handoffs:
            context = self.active_handoffs[handoff_id]
            context.add_metadata('completed', True)
            context.add_metadata('success', success)
            context.add_metadata('completion_time', datetime.now().isoformat())
            del self.active_handoffs[handoff_id]
            return True
        return False

    def get_handoff_status(self, handoff_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a handoff."""
        if handoff_id in self.active_handoffs:
            context = self.active_handoffs[handoff_id]
            return {
                'id': handoff_id,
                'source': context.source_agent,
                'target': context.target_agent,
                'timestamp': context.timestamp.isoformat(),
                'metadata': context.metadata,
                'status': 'active'
            }
        return None

    def generate_report(self) -> GateReport:
        """Generate a report of handoff activities."""
        completed_handoffs = [h for h in self.handoffs if h.metadata.get('completed', False)]
        successful_handoffs = [h for h in completed_handoffs if h.metadata.get('success', False)]
        
        success_rate = len(successful_handoffs) / len(completed_handoffs) if completed_handoffs else 0.0
        avg_duration = 0.0  # Calculate average duration if needed
        
        return GateReport(
            handoff_count=len(self.handoffs),
            success_rate=success_rate,
            avg_duration=avg_duration
        )