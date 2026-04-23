#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Add project root to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
)

@dataclass
class GateReport:
    """Report from the agent handoff gate analysis"""
    has_policy_changes: bool
    policy_changes: List[str]
    recommendations: List[str]
    risk_level: str

def parse_changed_paths(changes_file: str) -> List[str]:
    """Parse changed file paths from a changes file"""
    if not Path(changes_file).exists():
        return []
    
    with open(changes_file, 'r') as f:
        changes_data = json.load(f)

    # Extract file paths from the changes data
    changed_files = []
    if isinstance(changes_data, list):
        # If it's a list of file paths
        changed_files = [str(item) for item in changes_data if isinstance(item, str)]
    elif isinstance(changes_data, dict) and 'files' in changes_data:
        changed_files = changes_data['files']

    return changed_files

def check_policy_changes(changed_paths: List[str]) -> tuple[bool, List[str]]:
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
    return has_changes, policy_changes

def generate_handoff_report(changed_paths: List[str]) -> GateReport:
    """Generate a comprehensive handoff report"""
    has_policy_changes, policy_changes = check_policy_changes(changed_paths)
    
    recommendations = []
    risk_level = "LOW"
    
    if has_policy_changes:
        risk_level = "HIGH"
        recommendations.append("Manual review required for policy changes")
        recommendations.append("Verify compliance with trading regulations")
    
    # Check for other high-risk patterns
    high_risk_patterns = ['trading', 'execution', 'order', 'position']
    for path in changed_paths:
        if any(pattern in path.lower() for pattern in high_risk_patterns):
            if risk_level == "LOW":
                risk_level = "MEDIUM"
            recommendations.append(f"Review trading logic changes in: {path}")
    
    if not recommendations:
        recommendations.append("No high-risk changes detected")
    
    return GateReport(
        has_policy_changes=has_policy_changes,
        policy_changes=policy_changes,
        recommendations=recommendations,
        risk_level=risk_level
    )

def main():
    """Main entry point for the agent handoff gate"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent handoff gate analysis")
    parser.add_argument("--changes-file", required=True, help="Path to changes file")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    # Parse changed paths
    changed_paths = parse_changed_paths(args.changes_file)
    
    # Generate report
    report = generate_handoff_report(changed_paths)
    
    # Output report
    report_data = {
        "has_policy_changes": report.has_policy_changes,
        "policy_changes": report.policy_changes,
        "recommendations": report.recommendations,
        "risk_level": report.risk_level
    }
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report_data, f, indent=2)
    else:
        print(json.dumps(report_data, indent=2))

if __name__ == "__main__":
    main()