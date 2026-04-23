#!/usr/bin/env python3
"""
Agent Handoff Gate - Validates agent handoff configurations and generates reports.
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.handoff_governance import (
    append_handoff_audit_record,
    build_delegation_contract,
    infer_risk_tier,
    validate_delegation_contract,
)
from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    collect_trading_policy_ab_metrics,
)

REQUIRED_AGENTS_SECTIONS = (
    "primary_agent",
    "secondary_agent", 
    "handoff_triggers",
    "risk_limits"
)

class GateReport:
    """Report class for gate validation results."""
    
    def __init__(self, status, message, details=None):
        self.status = status
        self.message = message
        self.details = details or {}

def parse_changed_files(changed_files_str):
    """Parse changed files string into a list."""
    if not changed_files_str:
        return []

    # Handle different formats: newline-separated, comma-separated, or space-separated
    changed_files_str = changed_files_str.strip()
    
    # Try newline separation first
    if '\n' in changed_files_str:
        files = changed_files_str.split('\n')
    # Then comma separation
    elif ',' in changed_files_str:
        files = changed_files_str.split(',')
    # Finally space separation
    else:
        files = changed_files_str.split()
    
    return [f.strip() for f in files if f.strip()]

def validate_agent_config(config_path):
    """Validate agent configuration file."""
    if not os.path.exists(config_path):
        return {"valid": False, "error": f"Config file not found: {config_path}"}

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"Invalid JSON: {e}"}

    # Check required sections
    missing_sections = []
    for section in REQUIRED_AGENTS_SECTIONS:
        if section not in config:
            missing_sections.append(section)

    if missing_sections:
        return {"valid": False, "error": f"Missing required sections: {missing_sections}"}

    return {"valid": True, "config": config}

def run_handoff_gate(changed_files=None):
    """Main gate function."""
    try:
        # Parse changed files
        if isinstance(changed_files, str):
            changed_files = parse_changed_files(changed_files)
        elif changed_files is None:
            changed_files = []

        # Find agent config files
        config_files = []
        for file_path in changed_files:
            if file_path.endswith('.json') and 'agent' in file_path.lower():
                config_files.append(file_path)

        # If no agent configs changed, pass
        if not config_files:
            return GateReport("pass", "No agent configurations changed")

        # Validate each config
        validation_results = []
        for config_file in config_files:
            result = validate_agent_config(config_file)
            validation_results.append({
                "file": config_file,
                "result": result
            })

        # Check if all validations passed
        failed_validations = [v for v in validation_results if not v["result"]["valid"]]
        
        if failed_validations:
            error_details = {v["file"]: v["result"]["error"] for v in failed_validations}
            return GateReport("fail", "Agent configuration validation failed", error_details)

        return GateReport("pass", "All agent configurations valid", 
                         {"validated_files": config_files})

    except Exception as e:
        return GateReport("fail", f"Gate execution failed: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Handoff Gate")
    parser.add_argument("--changed-files", help="Changed files (newline, comma, or space separated)")
    
    args = parser.parse_args()
    
    result = run_handoff_gate(args.changed_files)
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    if result.details:
        print(f"Details: {result.details}")
    
    sys.exit(0 if result.status == "pass" else 1)