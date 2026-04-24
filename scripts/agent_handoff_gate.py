import subprocess
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class GateStepResult:
    """Result of a gate evaluation step"""
    passed: bool
    risk_level: str
    message: str
    recommendations: List[str]

@dataclass
class GateReport:
    """Complete gate evaluation report"""
    overall_passed: bool
    risk_level: str
    steps: List[GateStepResult]
    recommendations: List[str]

def get_changed_files() -> List[str]:
    """
    Get list of changed files from git diff

    Returns:
        List of file paths that have been changed
    """
    try:
        result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1'],
                              capture_output=True, text=True)
        git_diff_output = result.stdout
    except Exception:
        return []

    changed_files = []
    lines = git_diff_output.strip().split('\n')
    for line in lines:
        file_path = line.strip()
        if file_path:
            changed_files.append(file_path)

    return changed_files

def assess_risk_level(changed_files: List[str]) -> GateStepResult:
    """
    Assess the risk level of changed files

    Args:
        changed_files: List of file paths that have been changed

    Returns:
        GateStepResult with risk assessment
    """
    if not changed_files:
        return GateStepResult(True, "LOW", "No files changed", [])

    risk_level = "LOW"
    recommendations = []

    high_risk_patterns = [
        "src/core/",
        "src/trading/",
        "requirements.txt",
        "pyproject.toml",
        "Dockerfile"
    ]

    medium_risk_patterns = [
        "src/",
        "tests/",
        ".github/"
    ]

    for file_path in changed_files:
        if any(pattern in file_path for pattern in high_risk_patterns):
            risk_level = "HIGH"
            recommendations.append(f"High-risk file modified: {file_path}")
        elif any(pattern in file_path for pattern in medium_risk_patterns):
            if risk_level == "LOW":
                risk_level = "MEDIUM"
            recommendations.append(f"Medium-risk file modified: {file_path}")

    passed = risk_level in ["LOW", "MEDIUM"]
    message = f"Risk assessment complete: {risk_level} risk level"

    return GateStepResult(passed, risk_level, message, recommendations)

def run_gate_evaluation() -> GateReport:
    """
    Run complete gate evaluation

    Returns:
        GateReport with evaluation results
    """
    steps = []
    all_recommendations = []

    # Step 1: Get changed files
    changed_files = get_changed_files()

    # Step 2: Assess risk
    risk_step = assess_risk_level(changed_files)
    steps.append(risk_step)
    all_recommendations.extend(risk_step.recommendations)

    # Determine overall result
    overall_passed = all(step.passed for step in steps)
    overall_risk = max([step.risk_level for step in steps], key=lambda x: ["LOW", "MEDIUM", "HIGH"].index(x))

    return GateReport(
        overall_passed=overall_passed,
        risk_level=overall_risk,
        steps=steps,
        recommendations=all_recommendations
    )