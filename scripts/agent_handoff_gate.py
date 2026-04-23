#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

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

def load_changes(changes_file: str) -> List[str]:
    if not os.path.exists(changes_file):
        return []
    
    with open(changes_file, 'r') as f:
        changes_data = json.load(f)

    if isinstance(changes_data, list):
        return changes_data
    elif isinstance(changes_data, dict) and 'changed_files' in changes_data:
        return changes_data['changed_files']
    else:
        return []

def analyze_policy_changes(changed_paths: List[str]) -> Dict[str, any]:
    """
    Check if any changed files are policy-related
    """
    policy_paths = set(DEFAULT_POLICY_DOC_PATHS)
    changed_set = set(changed_paths)

    policy_changes = policy_paths.intersection(changed_set)

    return {
        'has_policy_changes': len(policy_changes) > 0,
        'policy_changes': list(policy_changes),
        'total_changes': len(changed_paths)
    }

def main():
    """Main entry point for the agent handoff gate"""
    changes_file = os.getenv('CHANGES_FILE', '.github/changed_files.json')
    
    changed_paths = load_changes(changes_file)
    
    # Check for critical config changes
    critical_configs = [
        'config/trading_config.yaml'
    ]

    analysis = analyze_policy_changes(changed_paths)
    
    report = GateReport(
        has_policy_changes=analysis['has_policy_changes'],
        policy_changes=analysis['policy_changes'],
        changed_paths=changed_paths
    )
    
    # Output results
    if report.has_policy_changes:
        print("POLICY CHANGES DETECTED")
        print(f"Changed policy files: {report.policy_changes}")
        return 1
    else:
        print("NO POLICY CHANGES")
        return 0

if __name__ == "__main__":
    sys.exit(main())