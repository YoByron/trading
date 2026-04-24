#!/usr/bin/env python3
"""Agent handoff gate for assessing change risk and providing recommendations."""

import re
import subprocess
from typing import List, Dict, Any
from dataclasses import dataclass


def parse_changed_paths(git_diff_output: str) -> List[str]:
    """Parse git diff output to extract changed file paths.

    Args:
        git_diff_output: Raw output from git diff command

    Returns:
        List of changed file paths
    """
    changed_files = []
    lines = git_diff_output.strip().split('\n')
    
    for line in lines:
        if line.startswith('+++') or line.startswith('---'):
            # Extract file path from git diff header
            if not line.endswith('/dev/null'):
                file_path = line[4:]  # Remove '+++ ' or '--- '
                if file_path not in changed_files and not file_path.startswith('b/'):
                    changed_files.append(file_path)
    
    return changed_files


@dataclass
class GateStepResult:
    """Result from a gate assessment step."""
    status: str
    risk_level: str
    recommendations: List[str]
    details: Dict[str, Any]


@dataclass
class GateReport:
    """Comprehensive gate assessment report."""
    overall_status: str
    risk_assessment: GateStepResult
    test_results: Dict[str, Any]
    recommendations: List[str]
    timestamp: str


def assess_handoff_risk(changed_files: List[str]) -> GateStepResult:
    """Assess risk level based on changed files.

    Args:
        changed_files: List of file paths that have changed

    Returns:
        GateStepResult with risk assessment
    """
    
    risk_level = "LOW"
    recommendations = []

    # Patterns that indicate higher risk
    high_risk_patterns = [
        r'requirements\.txt',
        r'setup\.py',
        r'Dockerfile',
        r'\.github/',
        r'pyproject\.toml'
    ]

    medium_risk_patterns = [
        r'src/',
        r'scripts/',
        r'\.py$'
    ]

    for file_path in changed_files:
        for pattern in high_risk_patterns:
            if re.search(pattern, file_path):
                risk_level = "HIGH"
                recommendations.append(f"High-risk file changed: {file_path}")
                break
        
        if risk_level != "HIGH":
            for pattern in medium_risk_patterns:
                if re.search(pattern, file_path):
                    risk_level = "MEDIUM"
                    recommendations.append(f"Medium-risk file changed: {file_path}")
                    break
    
    if not recommendations:
        recommendations = ["Low risk changes detected"]
    
    return GateStepResult(
        status="ASSESSED",
        risk_level=risk_level,
        recommendations=recommendations,
        details={"changed_files": changed_files}
    )


def run_gate_assessment() -> GateReport:
    """Run comprehensive gate assessment."""
    try:
        # Get changed files from git
        result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1'], 
                               capture_output=True, text=True)
        changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        # Assess risk
        risk_assessment = assess_handoff_risk(changed_files)
        
        return GateReport(
            overall_status="COMPLETE",
            risk_assessment=risk_assessment,
            test_results={"status": "pending"},
            recommendations=risk_assessment.recommendations,
            timestamp="2024-01-01T00:00:00Z"
        )
    
    except Exception as e:
        return GateReport(
            overall_status="ERROR",
            risk_assessment=GateStepResult("ERROR", "UNKNOWN", [str(e)], {}),
            test_results={"status": "error", "message": str(e)},
            recommendations=[f"Error during assessment: {str(e)}"],
            timestamp="2024-01-01T00:00:00Z"
        )


if __name__ == "__main__":
    report = run_gate_assessment()
    print(f"Gate Assessment: {report.overall_status}")
    print(f"Risk Level: {report.risk_assessment.risk_level}")
    for rec in report.recommendations:
        print(f"- {rec}")