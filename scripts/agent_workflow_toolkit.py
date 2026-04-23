#!/usr/bin/env python3
"""
Agent Workflow Toolkit
Provides utilities for agent workflow management and retrospective capture.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

class RetroCapture:
    def __init__(self, workflow_id: str, agent_name: str):
        self.workflow_id = workflow_id
        self.agent_name = agent_name
        self.start_time = datetime.now()
        self.end_time = None
        self.actions = []
        self.outcomes = {}
        self.lessons_learned = []

    def add_action(self, action_type: str, description: str, metadata: Dict[str, Any] = None):
        """Record an action taken during the workflow"""
        action = {
            'timestamp': datetime.now().isoformat(),
            'type': action_type,
            'description': description,
            'metadata': metadata or {}
        }
        self.actions.append(action)

    def add_outcome(self, key: str, value: Any):
        """Record an outcome from the workflow"""
        self.outcomes[key] = value

    def add_lesson(self, lesson: str, category: str = 'general'):
        """Add a lesson learned during the workflow"""
        self.lessons_learned.append({
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'lesson': lesson
        })

    def finalize(self):
        """Mark the workflow as complete"""
        self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'workflow_id': self.workflow_id,
            'agent_name': self.agent_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'actions': self.actions,
            'outcomes': self.outcomes,
            'lessons_learned': self.lessons_learned
        }

def create_retro_capture(workflow_id: str, agent_name: str) -> RetroCapture:
    """Create a new retrospective capture instance"""
    return RetroCapture(workflow_id, agent_name)

def save_retro_capture(retro: RetroCapture, output_dir: str = ".github/workflow_retros"):
    """Save retrospective capture to file"""
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{retro.workflow_id}_{retro.agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(retro.to_dict(), f, indent=2)
    
    return filepath

def load_retro_capture(filepath: str) -> RetroCapture:
    """Load retrospective capture from file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    retro = RetroCapture(data['workflow_id'], data['agent_name'])
    retro.start_time = datetime.fromisoformat(data['start_time'])
    if data.get('end_time'):
        retro.end_time = datetime.fromisoformat(data['end_time'])
    retro.actions = data.get('actions', [])
    retro.outcomes = data.get('outcomes', {})
    retro.lessons_learned = data.get('lessons_learned', [])
    
    return retro

def main():
    """Example usage of the workflow toolkit"""
    # Create a sample retrospective
    retro = create_retro_capture("test_workflow_001", "trading_agent")
    
    retro.add_action("analysis", "Analyzed market conditions")
    retro.add_action("decision", "Made trading decision")
    retro.add_outcome("trade_executed", True)
    retro.add_outcome("profit_loss", 150.50)
    retro.add_lesson("Market volatility was higher than expected", "market_analysis")
    
    retro.finalize()
    
    # Save the retrospective
    filepath = save_retro_capture(retro)
    print(f"Retrospective saved to: {filepath}")
    
    # Load it back to verify
    loaded_retro = load_retro_capture(filepath)
    print(f"Loaded workflow: {loaded_retro.workflow_id}")
    print(f"Actions taken: {len(loaded_retro.actions)}")
    print(f"Lessons learned: {len(loaded_retro.lessons_learned)}")

if __name__ == "__main__":
    main()