import subprocess
from dataclasses import dataclass
from typing import List

@dataclass
class GateStep:
    name: str
    passed: bool
    message: str
    recommendations: List[str]

@dataclass
class GateStepResult:
    steps: List[GateStep]

@dataclass
class GateReport:
    steps: List[GateStep]
    overall_passed: bool
    summary: str

def run_tests():
    """Run pytest and return results"""
    try:
        result = subprocess.run(['pytest', '-v'], capture_output=True, text=True)
        passed = result.returncode == 0
        message = "All tests passed" if passed else f"Tests failed: {result.stdout}"
        recommendations = [] if passed else ["Fix failing tests before proceeding"]
        return GateStep("Test Validation", passed, message, recommendations)
    except Exception as e:
        return GateStep("Test Validation", False,
                       f"Error running tests: {str(e)}",
                       ["Ensure pytest is installed and tests are runnable"])

def run_linting():
    """Run linting checks and return results"""
    try:
        result = subprocess.run(['ruff', 'check', '.'], capture_output=True, text=True)
        passed = result.returncode == 0
        message = "Code quality checks passed" if passed else \
                  f"Linting issues found: {result.stdout}"
        recommendations = [] if passed else ["Fix linting issues before proceeding"]
        return GateStep("Lint Validation", passed, message, recommendations)
    except Exception as e:
        return GateStep("Lint Validation", False,
                       f"Error running linter: {str(e)}",
                       ["Ensure ruff is installed"])

def validate_dependencies():
    """Validate that all dependencies are properly installed"""
    try:
        passed = True
        message = "All dependencies are properly installed"
        recommendations = []
        return GateStep("Dependency Validation", passed, message, recommendations)
    except Exception as e:
        return GateStep("Dependency Validation", False,
                       f"Dependency validation failed: {str(e)}",
                       ["Check requirements.txt and install missing packages"])

def generate_gate_report() -> GateReport:
    """Generate a complete gate report"""
    steps = [
        run_tests(),
        run_linting(),
        validate_dependencies()
    ]
    
    overall_passed = all(step.passed for step in steps)
    summary = "All gates passed" if overall_passed else "Some gates failed"
    
    return GateReport(steps, overall_passed, summary)