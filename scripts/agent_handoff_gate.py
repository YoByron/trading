#!/usr/bin/env python3
"""
Agent handoff gate for trading system operations.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
)


def parse_changed_paths(changes_file: str) -> List[str]:
    """Parse changed file paths from changes file."""
    try:
        with open(changes_file, 'r') as f:
            changes_data = json.load(f)
        
        if isinstance(changes_data, list):
            return changes_data
        elif isinstance(changes_data, dict) and 'files' in changes_data:
            return changes_data['files']
        else:
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def analyze_policy_impact(changed_paths: List[str]) -> Dict[str, any]:
    """Analyze impact of changes on trading policies."""
    policy_paths = set(DEFAULT_POLICY_DOC_PATHS)
    changed_set = set(changed_paths)
    
    policy_changes = policy_paths.intersection(changed_set)
    
    return {
        'has_policy_changes': len(policy_changes) > 0,
        'changed_policies': list(policy_changes),
        'risk_level': 'high' if policy_changes else 'low'
    }


def check_critical_files(changed_paths: List[str]) -> Dict[str, any]:
    """Check if any critical trading files were changed."""
    critical_patterns = [
        'src/trading/',
        'src/portfolio/',
        'src/risk/',
        'src/execution/',
        'config/trading_config.yaml'
    ]
    
    critical_changes = []
    for path in changed_paths:
        for pattern in critical_patterns:
            if pattern in path:
                critical_changes.append(path)
                break
    
    return {
        'has_critical_changes': len(critical_changes) > 0,
        'changed_files': critical_changes,
        'requires_review': len(critical_changes) > 0
    }


def validate_handoff_criteria(changed_paths: List[str]) -> Dict[str, any]:
    """Validate if handoff criteria are met."""
    policy_analysis = analyze_policy_impact(changed_paths)
    critical_analysis = check_critical_files(changed_paths)
    
    # Determine if handoff should proceed
    can_handoff = True
    blocking_issues = []
    
    if policy_analysis['has_policy_changes']:
        can_handoff = False
        blocking_issues.append("Policy changes detected - requires human review")
    
    if critical_analysis['requires_review']:
        can_handoff = False
        blocking_issues.append("Critical trading files modified - requires review")
    
    return {
        'can_handoff': can_handoff,
        'blocking_issues': blocking_issues,
        'policy_analysis': policy_analysis,
        'critical_analysis': critical_analysis,
        'recommendation': 'proceed' if can_handoff else 'hold_for_review'
    }


def run_handoff_gate(changes_file: str) -> bool:
    """Run the agent handoff gate process."""
    print("🚪 Running Agent Handoff Gate...")
    
    # Parse changed paths
    changed_paths = parse_changed_paths(changes_file)
    if not changed_paths:
        print("ℹ️  No changes detected - handoff approved")
        return True
    
    print(f"📝 Analyzing {len(changed_paths)} changed files...")
    
    # Validate handoff criteria
    validation_result = validate_handoff_criteria(changed_paths)
    
    # Output results
    if validation_result['can_handoff']:
        print("✅ Handoff gate PASSED - proceeding with agent handoff")
        print(f"   Recommendation: {validation_result['recommendation']}")
        return True
    else:
        print("🛑 Handoff gate FAILED - blocking agent handoff")
        print("   Blocking issues:")
        for issue in validation_result['blocking_issues']:
            print(f"   - {issue}")
        print(f"   Recommendation: {validation_result['recommendation']}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Agent handoff gate for trading system")
    parser.add_argument(
        "--changes-file",
        required=True,
        help="Path to file containing changed file paths"
    )
    
    args = parser.parse_args()
    success = run_handoff_gate(args.changes_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()