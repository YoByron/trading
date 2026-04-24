import subprocess
from dataclasses import dataclass
from typing import List

@dataclass
class GateStep:
    name: str
    passed: bool
    risk_level: str
    message: str
    recommendations: List[str]

@dataclass
class GateReport:
    overall_passed: bool
    overall_risk: str
    steps: List[GateStep]
    recommendations: List[str]

def parse_changed_paths(git_diff_output: str) -> List[str]:
    """Parse git diff output to extract changed file paths."""
    paths = []
    for line in git_diff_output.split('\n'):
        if line.startswith('diff --git'):
            # Extract path from "diff --git a/path b/path" format
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3][2:]  # Remove "b/" prefix
                paths.append(path)
    return paths

def validate_code_quality() -> GateStep:
    """Run code quality checks using flake8."""
    try:
        result = subprocess.run(['flake8', '.'], capture_output=True, text=True)
        if result.returncode == 0:
            return GateStep(
                name="Code Quality",
                passed=True,
                risk_level="LOW",
                message="All code quality checks passed",
                recommendations=[]
            )
        else:
            return GateStep(
                name="Code Quality",
                passed=False,
                risk_level="MEDIUM",
                message=f"Code quality issues found: {result.stdout}",
                recommendations=["Fix linting issues before deployment"]
            )
    except Exception as e:
        return GateStep(
            name="Code Quality",
            passed=False,
            risk_level="HIGH",
            message=f"Failed to run code quality checks: {e}",
            recommendations=["Ensure flake8 is installed and accessible"]
        )

def validate_tests() -> GateStep:
    """Run test suite validation."""
    try:
        result = subprocess.run(['python', '-m', 'pytest', '-v'], capture_output=True, text=True)
        if result.returncode == 0:
            return GateStep(
                name="Test Validation",
                passed=True,
                risk_level="LOW",
                message="All tests passed",
                recommendations=[]
            )
        else:
            return GateStep(
                name="Test Validation",
                passed=False,
                risk_level="HIGH",
                message=f"Test failures detected: {result.stdout}",
                recommendations=["Fix failing tests before deployment"]
            )
    except Exception as e:
        return GateStep(
            name="Test Validation",
            passed=False,
            risk_level="HIGH",
            message=f"Failed to run tests: {e}",
            recommendations=["Ensure pytest is installed and tests are accessible"]
        )

def validate_security() -> GateStep:
    """Run security validation checks."""
    # Simple security check - look for common patterns
    security_issues = []
    
    # Check for hardcoded credentials (basic check)
    try:
        result = subprocess.run(['grep', '-r', 'password=', '.', '--exclude-dir=.git'], 
                              capture_output=True, text=True)
        if result.stdout:
            security_issues.append("Potential hardcoded passwords found")
    except:
        pass
    
    if security_issues:
        return GateStep(
            name="Security Validation",
            passed=False,
            risk_level="HIGH",
            message=f"Security issues found: {', '.join(security_issues)}",
            recommendations=["Review and remove hardcoded credentials"]
        )
    else:
        return GateStep(
            name="Security Validation",
            passed=True,
            risk_level="LOW",
            message="No security issues detected",
            recommendations=[]
        )

def run_gate_validation() -> GateReport:
    """Run all gate validation steps."""
    steps = [
        validate_code_quality(),
        validate_tests(),
        validate_security()
    ]
    
    # Collect all recommendations
    all_recommendations = []
    for step in steps:
        all_recommendations.extend(step.recommendations)
    
    # Determine overall result
    overall_passed = all(step.passed for step in steps)
    overall_risk = max([step.risk_level for step in steps], 
                      key=lambda x: ["LOW", "MEDIUM", "HIGH"].index(x))
    
    return GateReport(
        overall_passed=overall_passed,
        overall_risk=overall_risk,
        steps=steps,
        recommendations=all_recommendations
    )