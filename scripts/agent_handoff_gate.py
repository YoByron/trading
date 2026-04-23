#!/usr/bin/env python3
"""
Agent Handoff Gate Script
Checks if changed files require human review before agent handoff.
"""

import json
import os
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
)

class GateReport:
    def __init__(self, has_policy_changes: bool, policy_changes: List[str],
                 changed_paths: List[str]):
        self.has_policy_changes = has_policy_changes
        self.policy_changes = policy_changes
        self.changed_paths = changed_paths

class GateStepResult:
    def __init__(self, success: bool, message: str, report: GateReport = None):
        self.success = success
        self.message = message
        self.report = report

def load_changes(changes_file: str) -> List[str]:
    """Load changed file paths from JSON file"""
    if not os.path.exists(changes_file):
        return []

    with open(changes_file, 'r') as f:
        changes_data = json.load(f)
    
    # Extract file paths from the changes data
    changed_files = []
    if isinstance(changes_data, list):
        changed_files = changes_data
    elif isinstance(changes_data, dict) and 'files' in changes_data:
        changed_files = changes_data['files']
    
    return changed_files

def check_policy_changes(changed_paths: List[str]) -> GateReport:
    """Check if any changed files are policy-related"""
    policy_changes = []
    
    for path in changed_paths:
        # Check against default policy paths
        if path in DEFAULT_POLICY_DOC_PATHS:
            policy_changes.append(f"Policy document changed: {path}")
        
        # Check for other policy-related patterns
        if any(pattern in path.lower() for pattern in ['policy', 'compliance', 'risk']):
            policy_changes.append(f"Policy-related file changed: {path}")
    
    has_changes = len(policy_changes) > 0
    return GateReport(has_changes, policy_changes, changed_paths)

def main():
    """Main entry point for the agent handoff gate"""
    changes_file = os.getenv('CHANGES_FILE', '.github/changed_files.json')

    changed_paths = load_changes(changes_file)

    # Check for policy changes
    gate_report = check_policy_changes(changed_paths)
    
    if gate_report.has_policy_changes:
        print("❌ GATE BLOCKED: Policy changes detected")
        for change in gate_report.policy_changes:
            print(f"  - {change}")
        print("\nHuman review required before agent handoff.")
        return GateStepResult(False, "Policy changes require human review", gate_report)
    
    print("✅ GATE PASSED: No policy changes detected")
    print(f"Changed files: {len(changed_paths)}")
    for path in changed_paths[:5]:  # Show first 5
        print(f"  - {path}")
    if len(changed_paths) > 5:
        print(f"  ... and {len(changed_paths) - 5} more")
    
    return GateStepResult(True, "No policy changes detected", gate_report)

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.success else 1)