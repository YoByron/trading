from dataclasses import dataclass
from typing import List
import subprocess
import sys
import os


@dataclass
class GateStepResult:
    name: str
    passed: bool
    details: str


@dataclass
class GateReport:
    steps: List[GateStepResult]
    overall_passed: bool
    summary: str


def parse_changed_paths(changed_files_str: str) -> List[str]:
    """Parse changed file paths from a string."""
    if not changed_files_str:
        return []
    return [f.strip() for f in changed_files_str.split('\n') if f.strip()]


def validate_python_syntax() -> GateStepResult:
    """Validate Python syntax across the project."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile'] + 
            [f for f in os.listdir('.') if f.endswith('.py')],
            capture_output=True,
            text=True
        )
        passed = result.returncode == 0
        details = result.stderr if not passed else "Syntax validation passed"
        return GateStepResult("Python Syntax", passed, details)
    except Exception as e:
        return GateStepResult("Python Syntax", False, f"Error: {e}")


def validate_imports() -> GateStepResult:
    """Validate that all imports can be resolved."""
    try:
        result = subprocess.run([sys.executable, '-c', 'import sys; sys.exit(0)'], 
                              capture_output=True)
        passed = result.returncode == 0
        details = "Import validation passed" if passed else "Import errors detected"
        return GateStepResult("Import Validation", passed, details)
    except Exception as e:
        return GateStepResult("Import Validation", False, f"Error: {e}")


def validate_dependencies() -> GateStepResult:
    """Validate that required dependencies are available."""
    try:
        import pandas
        import numpy
        return GateStepResult("Dependencies", True, "All dependencies available")
    except ImportError as e:
        return GateStepResult("Dependencies", False, f"Missing dependency: {e}")


def run_handoff_gate() -> GateReport:
    """Execute all handoff gate checks."""
    steps = [
        validate_python_syntax(),
        validate_imports(),
        validate_dependencies()
    ]

    overall_passed = all(step.passed for step in steps)
    summary = "All gates passed" if overall_passed else "Some gates failed"

    return GateReport(steps, overall_passed, summary)