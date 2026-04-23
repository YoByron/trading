#!/usr/bin/env python3
"""
Agent Handoff Gate - Validates and executes agent delegation workflows.

This script manages the transition of trading responsibilities between human
operators and AI agents, ensuring proper authorization, risk assessment,
and fallback mechanisms are in place.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Setup path and imports
REPO_ROOT = Path(__file__).parent.parent
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
    "agent_config",
    "delegation_scope",
    "risk_parameters",
    "monitoring_config",
    "fallback_triggers"
)

REQUIRED_HANDOFF_SECTIONS = (
    "handoff_id",
    "from_operator",
    "to_agent",
    "delegation_scope",
    "risk_tier",
    "authorization_level",
    "start_time",
    "expected_duration",
    "fallback_plan"
)

def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the handoff gate."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                REPO_ROOT / "logs" / "agent_handoff_gate.log",
                mode="a"
            )
        ]
    )

def load_agents_config(config_path: Path) -> Dict:
    """Load and validate agents configuration."""
    logger = logging.getLogger(__name__)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Agents config not found: {config_path}")
    
    with open(config_path) as f:
        config = json.load(f)
    
    # Validate required sections
    missing_sections = [
        section for section in REQUIRED_AGENTS_SECTIONS
        if section not in config
    ]
    
    if missing_sections:
        raise ValueError(
            f"Missing required sections in agents config: {missing_sections}"
        )
    
    logger.info(f"✅ Loaded agents config from {config_path}")
    return config

def load_handoff_request(request_path: Path) -> Dict:
    """Load and validate handoff request."""
    logger = logging.getLogger(__name__)
    
    if not request_path.exists():
        raise FileNotFoundError(f"Handoff request not found: {request_path}")
    
    with open(request_path) as f:
        request = json.load(f)
    
    # Validate required sections
    missing_sections = [
        section for section in REQUIRED_HANDOFF_SECTIONS
        if section not in request
    ]
    
    if missing_sections:
        raise ValueError(
            f"Missing required sections in handoff request: {missing_sections}"
        )
    
    logger.info(f"✅ Loaded handoff request from {request_path}")
    return request

def validate_handoff_authorization(
    handoff_request: Dict,
    agents_config: Dict
) -> bool:
    """Validate that the handoff is properly authorized."""
    logger = logging.getLogger(__name__)
    
    # Check authorization level
    required_auth = agents_config["agent_config"].get(
        "required_authorization_level",
        "operator"
    )
    
    provided_auth = handoff_request.get("authorization_level", "none")
    
    auth_hierarchy = ["none", "operator", "supervisor", "admin"]
    
    if (auth_hierarchy.index(provided_auth) < 
        auth_hierarchy.index(required_auth)):
        logger.error(
            f"❌ Insufficient authorization: {provided_auth} < {required_auth}"
        )
        return False
    
    # Validate risk tier compatibility
    request_risk_tier = handoff_request.get("risk_tier", "unknown")
    max_risk_tier = agents_config["risk_parameters"].get(
        "max_risk_tier",
        "low"
    )
    
    risk_levels = ["low", "medium", "high", "critical"]
    
    if (risk_levels.index(request_risk_tier) > 
        risk_levels.index(max_risk_tier)):
        logger.error(
            f"❌ Risk tier too high: {request_risk_tier} > {max_risk_tier}"
        )
        return False
    
    logger.info("✅ Handoff authorization validated")
    return True

def execute_handoff_workflow(
    handoff_request: Dict,
    agents_config: Dict,
    dry_run: bool = False
) -> Dict:
    """Execute the complete handoff workflow."""
    logger = logging.getLogger(__name__)
    
    try:
        # Step 1: Infer risk tier from request
        risk_tier = infer_risk_tier(handoff_request)
        handoff_request["inferred_risk_tier"] = risk_tier
        
        # Step 2: Get required steps for this risk tier
        required_steps = required_step_names_for_tier(risk_tier)
        
        # Step 3: Build delegation contract
        delegation_contract = build_delegation_contract(
            handoff_request,
            agents_config,
            required_steps
        )
        
        # Step 4: Validate delegation contract
        validation_result = validate_delegation_contract(delegation_contract)
        
        if not validation_result["is_valid"]:
            raise ValueError(
                f"Invalid delegation contract: {validation_result['errors']}"
            )
        
        # Step 5: Build fallback plan
        fallback_plan = build_fallback_plan(
            handoff_request,
            agents_config
        )
        
        # Step 6: Collect policy drift metrics
        policy_metrics = collect_trading_policy_ab_metrics(
            DEFAULT_POLICY_DOC_PATHS
        )
        
        # Step 7: Execute handoff (unless dry run)
        if not dry_run:
            # Write policy metrics
            write_trading_policy_ab_metrics(policy_metrics)
            
            # Record handoff in audit log
            append_handoff_audit_record({
                "handoff_request": handoff_request,
                "delegation_contract": delegation_contract,
                "fallback_plan": fallback_plan,
                "policy_metrics": policy_metrics,
                "execution_timestamp": datetime.utcnow().isoformat(),
                "status": "executed"
            })
            
            logger.info("✅ Handoff executed successfully")
        else:
            logger.info("✅ Handoff validation completed (dry run)")
        
        return {
            "status": "success",
            "handoff_id": handoff_request["handoff_id"],
            "delegation_contract": delegation_contract,
            "fallback_plan": fallback_plan,
            "policy_metrics": policy_metrics,
            "dry_run": dry_run
        }
        
    except Exception as e:
        logger.error(f"❌ Handoff failed: {str(e)}")
        
        # Record failure in audit log
        if not dry_run:
            append_handoff_audit_record({
                "handoff_request": handoff_request,
                "error": str(e),
                "execution_timestamp": datetime.utcnow().isoformat(),
                "status": "failed"
            })
        
        raise

def main():
    """Main entry point for agent handoff gate."""
    parser = argparse.ArgumentParser(
        description="Validate and execute agent delegation workflows"
    )
    
    parser.add_argument(
        "--agents-config",
        type=Path,
        default=REPO_ROOT / "config" / "agents.json",
        help="Path to agents configuration file"
    )
    
    parser.add_argument(
        "--handoff-request",
        type=Path,
        required=True,
        help="Path to handoff request JSON file"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate handoff without executing"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to write handoff result JSON"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Starting agent handoff gate")
        
        # Load configurations
        agents_config = load_agents_config(args.agents_config)
        handoff_request = load_handoff_request(args.handoff_request)
        
        # Validate authorization
        if not validate_handoff_authorization(handoff_request, agents_config):
            sys.exit(1)
        
        # Execute handoff workflow
        result = execute_handoff_workflow(
            handoff_request,
            agents_config,
            dry_run=args.dry_run
        )
        
        # Write output if specified
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"✅ Result written to {args.output}")
        
        logger.info("🎯 Agent handoff gate completed successfully")
        
    except Exception as e:
        logger.error(f"💥 Agent handoff gate failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()