import sys
import subprocess
import os
from typing import List, NamedTuple
import importlib.util

class GateStepResult(NamedTuple):
    step_name: str
    passed: bool
    message: str

class GateReport(NamedTuple):
    steps: List[GateStepResult]
    overall_passed: bool
    summary: str

def validate_syntax():
    """Validate Python syntax for all .py files."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile'] +
            [f for f in os.listdir('.') if f.endswith('.py')],
            capture_output=True,
            text=True
        )
        passed = result.returncode == 0
        message = "Syntax validation passed" if passed else f"Syntax errors: {result.stderr}"
        return GateStepResult("Syntax", passed, message)
    except Exception as e:
        return GateStepResult("Syntax", False, f"Syntax validation failed: {str(e)}")

def validate_imports():
    """Validate that all imports can be resolved."""
    try:
        result = subprocess.run([sys.executable, '-c', 'import sys; sys.exit(0)'],
                              capture_output=True)
        passed = result.returncode == 0
        message = "Import validation passed" if passed else "Import validation failed"
        return GateStepResult("Imports", passed, message)
    except Exception as e:
        return GateStepResult("Imports", False, f"Import validation failed: {str(e)}")

def validate_dependencies():
    """Validate that required dependencies are available."""
    try:
        pandas_spec = importlib.util.find_spec("pandas")
        numpy_spec = importlib.util.find_spec("numpy")
        if pandas_spec is None or numpy_spec is None:
            return GateStepResult("Dependencies", False, "Required dependencies not available")
        return GateStepResult("Dependencies", True, "All dependencies available")
    except ImportError as e:
        return GateStepResult("Dependencies", False, f"Dependency check failed: {str(e)}")

def run_quality_gate():
    """Run all quality gate checks."""
    steps = []
    steps.append(validate_syntax())
    steps.append(validate_imports())
    steps.append(validate_dependencies())
    
    overall_passed = all(step.passed for step in steps)
    summary = "All gates passed" if overall_passed else "Some gates failed"

    return GateReport(steps, overall_passed, summary)

def render_markdown_report(report: GateReport) -> str:
    """Render a quality gate report as markdown."""
    lines = ["# Quality Gate Report", ""]
    
    for step in report.steps:
        status = "✅" if step.passed else "❌"
        lines.append(f"## {step.step_name} {status}")
        lines.append(f"{step.message}")
        lines.append("")
    
    lines.append(f"## Summary")
    lines.append(f"Overall Status: {'✅ PASSED' if report.overall_passed else '❌ FAILED'}")
    lines.append(f"{report.summary}")
    
    return "\n".join(lines)