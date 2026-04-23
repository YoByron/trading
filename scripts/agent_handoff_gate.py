#!/usr/bin/env python3
"""Agent handoff gate validation script."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add repo root to Python path for imports
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
    "## 🎯 Current Focus",
    "## 🔄 Status Update",
    "## 📊 Key Metrics",
    "## 🔄 Agent Transition",
    "## ⚠️ Risk Assessment", 
    "## 🎯 Next Steps"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GateStepResult:
    """Result of a gate validation step."""

    def __init__(self, step_name: str, passed: bool, message: str, details: Optional[Dict] = None):
        self.step_name = step_name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "step_name": self.step_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


def parse_changed_paths(changed_files_str: str) -> list:
    """Parse changed files string into list of paths."""
    if not changed_files_str or changed_files_str.strip() == '':
        return []
    
    # Split by newlines and filter out empty strings
    paths = [line.strip() for line in changed_files_str.strip().split('\n') if line.strip()]
    return paths


def validate_handoff_documentation(handoff_doc_path: str) -> GateStepResult:
    """Validate that handoff documentation exists and contains required sections."""
    try:
        doc_path = Path(handoff_doc_path)
        
        if not doc_path.exists():
            return GateStepResult(
                "handoff_documentation",
                False,
                f"Handoff documentation not found at {handoff_doc_path}"
            )
        
        content = doc_path.read_text()
        missing_sections = []
        
        for section in REQUIRED_AGENTS_SECTIONS:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            return GateStepResult(
                "handoff_documentation",
                False,
                f"Missing required sections: {', '.join(missing_sections)}",
                {"missing_sections": missing_sections}
            )
        
        return GateStepResult(
            "handoff_documentation",
            True,
            "All required sections present in handoff documentation"
        )
        
    except Exception as e:
        return GateStepResult(
            "handoff_documentation", 
            False,
            f"Error validating handoff documentation: {str(e)}"
        )


def validate_risk_assessment(changed_paths: list) -> GateStepResult:
    """Validate risk assessment based on changed files."""
    try:
        # Determine risk tier based on changed paths
        risk_tier = infer_risk_tier(changed_paths)
        
        return GateStepResult(
            "risk_assessment",
            True,
            f"Risk tier determined: {risk_tier}",
            {"risk_tier": risk_tier, "changed_paths": changed_paths}
        )
        
    except Exception as e:
        return GateStepResult(
            "risk_assessment",
            False,
            f"Error during risk assessment: {str(e)}"
        )


def validate_policy_compliance(changed_paths: list) -> GateStepResult:
    """Validate that changes comply with trading policies."""
    try:
        # Collect policy metrics for changed areas
        metrics = collect_trading_policy_ab_metrics(
            changed_paths=changed_paths,
            policy_doc_paths=DEFAULT_POLICY_DOC_PATHS
        )
        
        # Write metrics to file
        write_trading_policy_ab_metrics(metrics)
        
        # Check for any policy violations
        violations = []
        for metric in metrics.get('violations', []):
            violations.append(metric)
        
        if violations:
            return GateStepResult(
                "policy_compliance",
                False,
                f"Policy violations detected: {len(violations)}",
                {"violations": violations}
            )
        
        return GateStepResult(
            "policy_compliance",
            True,
            "No policy violations detected",
            {"metrics": metrics}
        )
        
    except Exception as e:
        return GateStepResult(
            "policy_compliance",
            False,
            f"Error validating policy compliance: {str(e)}"
        )


def validate_delegation_contract(contract_data: Dict) -> GateStepResult:
    """Validate delegation contract structure and content."""
    try:
        # Use the imported validation function
        is_valid, errors = validate_delegation_contract(contract_data)
        
        if not is_valid:
            return GateStepResult(
                "delegation_contract",
                False,
                f"Delegation contract validation failed: {'; '.join(errors)}",
                {"errors": errors}
            )
        
        return GateStepResult(
            "delegation_contract",
            True,
            "Delegation contract is valid"
        )
        
    except Exception as e:
        return GateStepResult(
            "delegation_contract",
            False,
            f"Error validating delegation contract: {str(e)}"
        )


def run_gate_validation(
    handoff_doc_path: str,
    changed_files: str,
    output_path: str = "gate_validation_results.json"
) -> Dict:
    """Run complete gate validation process."""
    results = []
    
    logger.info("Starting agent handoff gate validation...")
    
    # Parse changed files
    changed_paths = parse_changed_paths(changed_files)
    logger.info(f"Detected {len(changed_paths)} changed files")
    
    # Step 1: Validate handoff documentation
    logger.info("Validating handoff documentation...")
    doc_result = validate_handoff_documentation(handoff_doc_path)
    results.append(doc_result)
    
    # Step 2: Validate risk assessment  
    logger.info("Performing risk assessment...")
    risk_result = validate_risk_assessment(changed_paths)
    results.append(risk_result)
    
    # Step 3: Validate policy compliance
    logger.info("Checking policy compliance...")
    policy_result = validate_policy_compliance(changed_paths)
    results.append(policy_result)
    
    # Step 4: Build and validate delegation contract
    logger.info("Building delegation contract...")
    try:
        risk_tier = risk_result.details.get('risk_tier', 'LOW')
        contract_data = build_delegation_contract(
            from_agent="current",
            to_agent="next", 
            risk_tier=risk_tier,
            changed_paths=changed_paths
        )
        
        contract_result = validate_delegation_contract(contract_data)
        results.append(contract_result)
        
    except Exception as e:
        contract_result = GateStepResult(
            "delegation_contract",
            False, 
            f"Error building delegation contract: {str(e)}"
        )
        results.append(contract_result)
    
    # Compile final results
    all_passed = all(result.passed for result in results)
    
    final_results = {
        "gate_passed": all_passed,
        "timestamp": datetime.now().isoformat(),
        "steps": [result.to_dict() for result in results],
        "summary": {
            "total_steps": len(results),
            "passed_steps": sum(1 for r in results if r.passed),
            "failed_steps": sum(1 for r in results if not r.passed)
        }
    }
    
    # Save results to file
    output_file = Path(output_path)
    output_file.write_text(json.dumps(final_results, indent=2))
    
    # Append to audit record
    try:
        append_handoff_audit_record({
            "gate_validation": final_results,
            "changed_paths": changed_paths
        })
    except Exception as e:
        logger.warning(f"Failed to append audit record: {str(e)}")
    
    logger.info(f"Gate validation completed. Results saved to {output_path}")
    logger.info(f"Gate status: {'PASSED' if all_passed else 'FAILED'}")
    
    return final_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent handoff gate validation")
    parser.add_argument(
        "--handoff-doc", 
        required=True,
        help="Path to handoff documentation file"
    )
    parser.add_argument(
        "--changed-files",
        default="",
        help="Newline-separated list of changed files"
    )
    parser.add_argument(
        "--output",
        default="gate_validation_results.json",
        help="Output file for validation results"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_gate_validation(
            args.handoff_doc,
            args.changed_files, 
            args.output
        )
        
        # Exit with appropriate code
        exit_code = 0 if results["gate_passed"] else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Gate validation failed with error: {str(e)}")
        sys.exit(1)