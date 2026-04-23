#!/usr/bin/env python3
"""
Agent Handoff Gate - Coordinates safe handoffs between AI agents.

This script manages the transition of control between different AI agents
in the trading system, ensuring proper validation, audit trails, and
fallback mechanisms.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Setup path and imports
REPO_ROOT = Path(__file__).resolve().parents[1]
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

DEFAULT_AGENTS_CONFIG = Path("config/agents.json")
DEFAULT_HANDOFF_LOG = Path("logs/agent_handoffs.log")


class GateReport:
    """Report containing handoff gate analysis results."""
    
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.success = False
        self.risk_tier = None
        self.required_steps = []
        self.completed_steps = []
        self.missing_steps = []
        self.delegation_contract = None
        self.fallback_plan = None
        self.errors = []
        self.warnings = []
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "success": self.success,
            "risk_tier": self.risk_tier,
            "required_steps": self.required_steps,
            "completed_steps": self.completed_steps,
            "missing_steps": self.missing_steps,
            "delegation_contract": self.delegation_contract,
            "fallback_plan": self.fallback_plan,
            "errors": self.errors,
            "warnings": self.warnings
        }


def load_agents_config(config_path: Path = None) -> Dict:
    """Load and validate agents configuration."""
    logger = logging.getLogger(__name__)

    if not config_path.exists():
        raise FileNotFoundError(f"Agents config not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in agents config: {e}")

    # Validate required sections
    missing_sections = []
    for section in REQUIRED_AGENTS_SECTIONS:
        if section not in config:
            missing_sections.append(section)

    if missing_sections:
        raise ValueError(f"Missing required sections in agents config: {missing_sections}")

    logger.info(f"Loaded agents config with {len(config)} sections")
    return config


def analyze_handoff_readiness(
    source_agent: str,
    target_agent: str,
    context: Dict,
    config_path: Path = None
) -> GateReport:
    """Analyze if a handoff between agents can proceed safely."""
    logger = logging.getLogger(__name__)
    report = GateReport()

    try:
        # Load configuration
        if config_path is None:
            config_path = DEFAULT_AGENTS_CONFIG
        config = load_agents_config(config_path)

        # Infer risk tier from context
        report.risk_tier = infer_risk_tier(context)
        logger.info(f"Handoff risk tier: {report.risk_tier}")

        # Get required steps for this risk tier
        report.required_steps = required_step_names_for_tier(report.risk_tier)
        
        # Check which steps are completed (simplified check)
        # In real implementation, this would check actual completion status
        report.completed_steps = []  # TODO: Implement actual step checking
        
        # Identify missing steps
        report.missing_steps = [
            step for step in report.required_steps 
            if step not in report.completed_steps
        ]

        # Build delegation contract
        try:
            report.delegation_contract = build_delegation_contract(
                source_agent=source_agent,
                target_agent=target_agent,
                context=context,
                risk_tier=report.risk_tier
            )
            
            # Validate the contract
            validation_result = validate_delegation_contract(report.delegation_contract)
            if not validation_result.get("valid", False):
                report.errors.extend(validation_result.get("errors", []))
                
        except Exception as e:
            report.errors.append(f"Failed to build delegation contract: {e}")

        # Build fallback plan
        try:
            report.fallback_plan = build_fallback_plan(
                source_agent=source_agent,
                target_agent=target_agent,
                context=context,
                risk_tier=report.risk_tier
            )
        except Exception as e:
            report.errors.append(f"Failed to build fallback plan: {e}")

        # Determine if handoff can proceed
        report.success = (
            len(report.errors) == 0 and
            len(report.missing_steps) == 0 and
            report.delegation_contract is not None and
            report.fallback_plan is not None
        )

        if report.success:
            logger.info(f"Handoff gate PASSED: {source_agent} -> {target_agent}")
        else:
            logger.warning(f"Handoff gate FAILED: {source_agent} -> {target_agent}")
            logger.warning(f"Errors: {report.errors}")
            logger.warning(f"Missing steps: {report.missing_steps}")

    except Exception as e:
        report.errors.append(f"Gate analysis failed: {e}")
        report.success = False
        logger.error(f"Handoff gate analysis failed: {e}")

    return report


def execute_handoff(
    source_agent: str,
    target_agent: str,
    context: Dict,
    config_path: Path = None,
    log_path: Path = None
) -> bool:
    """Execute a complete agent handoff with validation and logging."""
    logger = logging.getLogger(__name__)

    # Analyze handoff readiness
    report = analyze_handoff_readiness(source_agent, target_agent, context, config_path)

    # Log the handoff attempt
    if log_path is None:
        log_path = DEFAULT_HANDOFF_LOG

    try:
        append_handoff_audit_record(
            log_path=log_path,
            source_agent=source_agent,
            target_agent=target_agent,
            context=context,
            success=report.success,
            details=report.to_dict()
        )
    except Exception as e:
        logger.error(f"Failed to log handoff: {e}")

    # Collect policy drift metrics
    try:
        policy_metrics = collect_trading_policy_ab_metrics(DEFAULT_POLICY_DOC_PATHS)
        write_trading_policy_ab_metrics(policy_metrics)
    except Exception as e:
        logger.warning(f"Failed to collect policy drift metrics: {e}")

    return report.success


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Agent Handoff Gate")
    parser.add_argument("source_agent", help="Source agent name")
    parser.add_argument("target_agent", help="Target agent name")
    parser.add_argument("--context", help="JSON context for handoff", default="{}")
    parser.add_argument("--config", help="Agents config path", type=Path)
    parser.add_argument("--log", help="Handoff log path", type=Path)
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze, don't execute")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        context = json.loads(args.context)
    except json.JSONDecodeError as e:
        print(f"Error parsing context JSON: {e}")
        return 1

    try:
        if args.analyze_only:
            report = analyze_handoff_readiness(
                args.source_agent,
                args.target_agent,
                context,
                args.config
            )
            print(json.dumps(report.to_dict(), indent=2))
            return 0 if report.success else 1
        else:
            success = execute_handoff(
                args.source_agent,
                args.target_agent,
                context,
                args.config,
                args.log
            )
            return 0 if success else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())