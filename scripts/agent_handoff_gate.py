import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
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
    "requesting_agent",
    "target_agent",
    "task_description",
    "risk_assessment",
    "expected_outcome",
    "fallback_plan",
    "timeout_seconds"
)


def parse_changed_paths(changed_files_str: str) -> list[str]:
    """Parse changed files from string input."""
    if not changed_files_str:
        return []
    
    # Handle different formats: newline-separated, comma-separated, or space-separated
    changed_files_str = changed_files_str.strip()
    if '\n' in changed_files_str:
        return [f.strip() for f in changed_files_str.split('\n') if f.strip()]
    elif ',' in changed_files_str:
        return [f.strip() for f in changed_files_str.split(',') if f.strip()]
    else:
        return [f.strip() for f in changed_files_str.split() if f.strip()]


def validate_handoff_config(config_path: str) -> Dict[str, Any]:
    """Validate handoff configuration file."""
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
        return {
            "valid": False,
            "error": f"Missing required sections: {missing_sections}"
        }
    
    return {"valid": True, "config": config}


def check_policy_drift() -> Dict[str, Any]:
    """Check for trading policy drift."""
    try:
        missing_sections = []
        for doc_path in DEFAULT_POLICY_DOC_PATHS:
            if not doc_path.exists():
                missing_sections.append(str(doc_path))
                continue
            
        content = doc_path.read_text()
        missing_sections.extend([])

        if missing_sections:
            return {
                "drift_detected": True,
                "missing_policies": missing_sections
            }
        
        # Collect metrics
        metrics = collect_trading_policy_ab_metrics()
        
        return {
            "drift_detected": False,
            "metrics": metrics
        }
        
    except Exception as e:
        return {
            "drift_detected": True,
            "error": str(e)
        }


def main():
    """Main entry point for agent handoff gate."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent handoff gate validation")
    parser.add_argument("--config", required=True, help="Path to handoff config file")
    parser.add_argument("--changed-files", help="Changed files to analyze")
    
    args = parser.parse_args()
    
    # Validate config
    validation_result = validate_handoff_config(args.config)
    if not validation_result["valid"]:
        print(f"Config validation failed: {validation_result['error']}")
        sys.exit(1)
    
    config = validation_result["config"]
    
    # Parse changed files
    changed_files = parse_changed_paths(args.changed_files or "")
    
    # Check policy drift
    drift_result = check_policy_drift()
    if drift_result["drift_detected"]:
        print(f"Policy drift detected: {drift_result}")
        sys.exit(1)
    
    # Infer risk tier
    risk_tier = infer_risk_tier(config, changed_files)
    
    # Build delegation contract
    contract = build_delegation_contract(config, risk_tier)
    
    # Validate contract
    contract_validation = validate_delegation_contract(contract)
    if not contract_validation["valid"]:
        print(f"Contract validation failed: {contract_validation}")
        sys.exit(1)
    
    # Append audit record
    append_handoff_audit_record(contract, datetime.now())
    
    print("Agent handoff gate validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())