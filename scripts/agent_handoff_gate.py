import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class HandoffContext:
    """Context for agent handoffs with metadata and state tracking."""
    
    def __init__(self, source_agent: str, target_agent: str):
        self.source_agent = source_agent
        self.target_agent = target_agent
        self.timestamp = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self.state_data: Dict[str, Any] = {}
        
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the handoff context."""
        self.metadata[key] = value
        
    def set_state(self, state: Dict[str, Any]):
        """Set the state data for handoff."""
        self.state_data = state

class AgentHandoffGate:
    """Gate for managing agent handoffs and transitions."""
    
    def __init__(self):
        self.handoffs: List[HandoffContext] = []
        self.active_agent: Optional[str] = None
        
    def initiate_handoff(self, source_agent: str, target_agent: str) -> HandoffContext:
        """Initiate a handoff between agents."""
        context = HandoffContext(source_agent, target_agent)
        self.handoffs.append(context)
        return context
        
    def complete_handoff(self, context: HandoffContext):
        """Complete the handoff and update active agent."""
        self.active_agent = context.target_agent
        
    def get_handoff_history(self) -> List[HandoffContext]:
        """Get the history of handoffs."""
        return self.handoffs

def analyze_handoff_patterns(gate: AgentHandoffGate) -> Dict[str, Any]:
    """Analyze patterns in agent handoffs."""
    handoffs = gate.get_handoff_history()
    if not handoffs:
        return {"total_handoffs": 0, "patterns": []}
    
    patterns = {}
    for handoff in handoffs:
        key = f"{handoff.source_agent}->{handoff.target_agent}"
        patterns[key] = patterns.get(key, 0) + 1
    
    return {
        "total_handoffs": len(handoffs),
        "patterns": patterns,
        "most_common": max(patterns.items(), key=lambda x: x[1]) if patterns else None
    }

def validate_handoff_sequence(sequence: List[str]) -> bool:
    """Validate a sequence of agent handoffs."""
    if len(sequence) < 2:
        return True
    
    # Check for cycles or invalid transitions
    seen = set()
    for i in range(len(sequence) - 1):
        transition = f"{sequence[i]}->{sequence[i+1]}"
        if transition in seen:
            return False  # Cycle detected
        seen.add(transition)
    
    return True

def render_markdown_report(gate: AgentHandoffGate) -> str:
    """Render a markdown report of handoff activities."""
    patterns = analyze_handoff_patterns(gate)
    
    report = "# Agent Handoff Report\n\n"
    report += f"**Total Handoffs:** {patterns['total_handoffs']}\n\n"
    
    if patterns['patterns']:
        report += "## Handoff Patterns\n\n"
        for pattern, count in patterns['patterns'].items():
            report += f"- {pattern}: {count} times\n"
        report += "\n"
    
    if patterns['most_common']:
        report += f"**Most Common Pattern:** {patterns['most_common'][0]} ({patterns['most_common'][1]} times)\n"
    
    return report

def parse_file_paths(paths_str: str) -> List[str]:
    """Parse file paths from a string."""
    if not paths_str:
        return []
    return [path.strip() for path in paths_str.split('\n') if path.strip()]