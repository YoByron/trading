import json
import sys
from pathlib import Path
from typing import List
from dataclasses import dataclass

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
)

@dataclass
class GateStepResult:
    step_name: str
    passed: bool
    message: str
    risk_level: str = "LOW"

def load_changes_from_file(changes_file: str = "changes.json") -> List[str]:
    """Load changed file paths from a JSON file"""
    if not Path(changes_file).exists():
        return []

    with open(changes_file, 'r') as f:
        changes_data = json.load(f)

    changed_paths = []
    if isinstance(changes_data, dict):
        if 'files' in changes_data:
            changed_paths.extend(changes_data['files'])
        if 'changed_files' in changes_data:
            changed_paths.extend(changes_data['changed_files'])
    elif isinstance(changes_data, list):
        changed_paths = changes_data

    return changed_paths

def check_policy_changes(changed_paths: List[str]) -> tuple[bool, List[str]]:
    """Check if any policy files were changed"""
    policy_changes = []

    for path in changed_paths:
        path_obj = Path(path)
        for policy_path in DEFAULT_POLICY_DOC_PATHS:
            if str(path_obj).startswith(str(policy_path)):
                policy_changes.append(path)
                break

    return len(policy_changes) > 0, policy_changes

def generate_handoff_report(changed_paths: List[str]) -> GateStepResult:
    """Generate a comprehensive handoff report"""
    has_policy_changes, policy_changes = check_policy_changes(changed_paths)

    recommendations = []
    risk_level = "LOW"

    if has_policy_changes:
        risk_level = "HIGH"
        recommendations.append("Manual review required for policy changes")
        recommendations.append("Verify compliance with trading regulations")

    if not changed_paths:
        return GateStepResult(
            step_name="handoff_gate",
            passed=True,
            message="No changes detected - proceeding with standard workflow",
            risk_level=risk_level
        )

    report_lines = [
        f"Files changed: {len(changed_paths)}",
        f"Policy files affected: {len(policy_changes)}",
        f"Risk level: {risk_level}"
    ]

    if recommendations:
        report_lines.append("Recommendations:")
        report_lines.extend(f"- {rec}" for rec in recommendations)

    return GateStepResult(
        step_name="handoff_gate",
        passed=risk_level != "HIGH",
        message="\n".join(report_lines),
        risk_level=risk_level
    )

def main():
    """Main entry point for agent handoff gate"""
    changed_paths = load_changes_from_file()
    result = generate_handoff_report(changed_paths)

    print(f"Handoff Gate Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Message:\n{result.message}")

    return 0 if result.passed else 1

if __name__ == "__main__":
    sys.exit(main())