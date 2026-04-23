#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add repo root to Python path for imports
SCRIPT_DIR = Path(__file__).parent.absolute()
REPO_ROOT = SCRIPT_DIR.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.handoff_governance import (
    append_handoff_audit_record,
    build_delegation_contract,
    build_fallback_plan,
    infer_risk_tier,
    required_step_names_for_tier,
    validate_delegation_contract,
)
from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
    collect_trading_policy_ab_metrics,
    write_trading_policy_ab_metrics,
)

REQUIRED_AGENTS_SECTIONS = (
    "market_analysis",
    "risk_management",
    "execution",
    "monitoring"
)

# Configuration file paths
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "agent_handoff_gate.json"
HANDOFF_LOG_PATH = REPO_ROOT / "logs" / "agent_handoffs.json"


class GateStepResult:
    """Result of a gate validation step."""
    
    def __init__(self, step_name: str, passed: bool, message: str = ""):
        self.step_name = step_name
        self.passed = passed
        self.message = message
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "step_name": self.step_name,
            "passed": self.passed,
            "message": self.message,
            "timestamp": self.timestamp
        }


class GateReport:
    """Report containing handoff gate analysis results."""

    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.policy_drift_metrics = {}
        self.handoff_validation = {}
        self.delegation_contract = {}
        self.fallback_plan = {}
        self.risk_tier = None
        self.required_steps = []
        self.completed_steps = []
        self.gate_results = []
        self.passed = False
        self.errors = []
        self.warnings = []

    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "policy_drift_metrics": self.policy_drift_metrics,
            "handoff_validation": self.handoff_validation,
            "delegation_contract": self.delegation_contract,
            "fallback_plan": self.fallback_plan,
            "risk_tier": self.risk_tier,
            "required_steps": self.required_steps,
            "completed_steps": self.completed_steps,
            "gate_results": [result.to_dict() for result in self.gate_results],
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings
        }


def load_handoff_config(config_path: Optional[Path] = None) -> Dict:
    """Load agent handoff gate configuration."""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    if not config_path.exists():
        logging.warning(f"Config file not found at {config_path}, using defaults")
        return {
            "risk_thresholds": {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8
            },
            "required_approvals": {
                "low": 1,
                "medium": 2,
                "high": 3
            },
            "timeout_seconds": 300
        }
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        raise


def analyze_trading_policy_drift(report: GateReport) -> None:
    """Analyze trading policy drift and add results to report."""
    try:
        # Collect policy drift metrics
        metrics = collect_trading_policy_ab_metrics(DEFAULT_POLICY_DOC_PATHS)
        report.policy_drift_metrics = metrics
        
        # Write metrics to output file
        write_trading_policy_ab_metrics(metrics)
        
        # Analyze drift severity
        drift_score = metrics.get("overall_drift_score", 0.0)
        if drift_score > 0.5:
            report.errors.append(f"High policy drift detected: {drift_score:.2f}")
            step_result = GateStepResult("policy_drift_check", False, 
                                       f"Drift score {drift_score:.2f} exceeds threshold")
        else:
            step_result = GateStepResult("policy_drift_check", True, 
                                       f"Drift score {drift_score:.2f} within acceptable range")
        
        report.gate_results.append(step_result)
        
    except Exception as e:
        error_msg = f"Failed to analyze policy drift: {e}"
        logging.error(error_msg)
        report.errors.append(error_msg)
        step_result = GateStepResult("policy_drift_check", False, error_msg)
        report.gate_results.append(step_result)


def validate_handoff_requirements(handoff_data: Dict, report: GateReport) -> None:
    """Validate handoff requirements and update report."""
    try:
        # Infer risk tier based on handoff data
        risk_tier = infer_risk_tier(handoff_data)
        report.risk_tier = risk_tier
        
        # Get required steps for this risk tier
        required_steps = required_step_names_for_tier(risk_tier)
        report.required_steps = required_steps
        
        # Validate delegation contract
        delegation_contract = build_delegation_contract(handoff_data)
        validation_result = validate_delegation_contract(delegation_contract)
        
        report.delegation_contract = delegation_contract
        report.handoff_validation = validation_result
        
        if validation_result.get("valid", False):
            step_result = GateStepResult("delegation_validation", True, 
                                       "Delegation contract is valid")
        else:
            errors = validation_result.get("errors", [])
            error_msg = f"Delegation validation failed: {errors}"
            report.errors.append(error_msg)
            step_result = GateStepResult("delegation_validation", False, error_msg)
        
        report.gate_results.append(step_result)
        
        # Build fallback plan
        fallback_plan = build_fallback_plan(handoff_data)
        report.fallback_plan = fallback_plan
        
        step_result = GateStepResult("fallback_plan", True, "Fallback plan generated")
        report.gate_results.append(step_result)
        
    except Exception as e:
        error_msg = f"Failed to validate handoff requirements: {e}"
        logging.error(error_msg)
        report.errors.append(error_msg)
        step_result = GateStepResult("handoff_validation", False, error_msg)
        report.gate_results.append(step_result)


def check_agent_readiness(handoff_data: Dict, report: GateReport) -> None:
    """Check if all required agents are ready for handoff."""
    try:
        agents_config = handoff_data.get("agents", {})
        
        for section in REQUIRED_AGENTS_SECTIONS:
            if section not in agents_config:
                error_msg = f"Missing required agent section: {section}"
                report.errors.append(error_msg)
                step_result = GateStepResult(f"agent_check_{section}", False, error_msg)
                report.gate_results.append(step_result)
                continue
            
            agent_config = agents_config[section]
            if not agent_config.get("enabled", False):
                warning_msg = f"Agent section {section} is disabled"
                report.warnings.append(warning_msg)
                step_result = GateStepResult(f"agent_check_{section}", False, warning_msg)
            else:
                step_result = GateStepResult(f"agent_check_{section}", True, 
                                           f"Agent {section} is ready")
            
            report.gate_results.append(step_result)
            
    except Exception as e:
        error_msg = f"Failed to check agent readiness: {e}"
        logging.error(error_msg)
        report.errors.append(error_msg)
        step_result = GateStepResult("agent_readiness", False, error_msg)
        report.gate_results.append(step_result)


def execute_handoff_gate(handoff_data: Dict, config_path: Optional[Path] = None) -> GateReport:
    """Execute the complete agent handoff gate process."""
    report = GateReport()
    
    try:
        # Load configuration
        load_handoff_config(config_path)
        
        # Step 1: Analyze trading policy drift
        analyze_trading_policy_drift(report)
        
        # Step 2: Validate handoff requirements
        validate_handoff_requirements(handoff_data, report)
        
        # Step 3: Check agent readiness
        check_agent_readiness(handoff_data, report)
        
        # Determine overall pass/fail status
        failed_steps = [r for r in report.gate_results if not r.passed]
        report.passed = len(failed_steps) == 0 and len(report.errors) == 0
        
        # Record handoff attempt
        handoff_record = {
            "timestamp": report.timestamp,
            "handoff_data": handoff_data,
            "gate_passed": report.passed,
            "errors": report.errors,
            "warnings": report.warnings
        }
        append_handoff_audit_record(handoff_record)
        
    except Exception as e:
        error_msg = f"Critical error in handoff gate execution: {e}"
        logging.error(error_msg)
        report.errors.append(error_msg)
        report.passed = False
    
    return report


def main():
    """Main entry point for agent handoff gate."""
    parser = argparse.ArgumentParser(description="Agent Handoff Gate")
    parser.add_argument("--config", type=Path, help="Path to configuration file")
    parser.add_argument("--handoff-data", type=Path, required=True,
                       help="Path to handoff data JSON file")
    parser.add_argument("--output", type=Path, 
                       help="Path to write gate report (default: stdout)")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load handoff data
        if not args.handoff_data.exists():
            logging.error(f"Handoff data file not found: {args.handoff_data}")
            sys.exit(1)
        
        with open(args.handoff_data, 'r') as f:
            handoff_data = json.load(f)
        
        # Execute handoff gate
        report = execute_handoff_gate(handoff_data, args.config)
        
        # Output results
        report_json = json.dumps(report.to_dict(), indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report_json)
            logging.info(f"Gate report written to {args.output}")
        else:
            print(report_json)
        
        # Exit with error code if gate failed
        if not report.passed:
            logging.error("Agent handoff gate FAILED")
            sys.exit(1)
        else:
            logging.info("Agent handoff gate PASSED")
            sys.exit(0)
            
    except Exception as e:
        logging.error(f"Failed to execute handoff gate: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()