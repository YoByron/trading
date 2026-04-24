"""Quality gate checker for agent handoffs."""

import os
import sys
import subprocess
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class GateStep:
    """Represents a single quality gate step."""
    name: str
    passed: bool
    message: str


@dataclass
class GateReport:
    """Complete quality gate report."""
    steps: List[GateStep]
    overall_passed: bool
    summary: str


def parse_changed_paths(changed_files_str: str) -> List[str]:
    """Parse changed file paths from a string."""
    if not changed_files_str:
        return []
    return [path.strip() for path in changed_files_str.split('\n') if path.strip()]


def validate_syntax() -> GateStep:
    """Validate Python syntax across the codebase."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', '-q', '.'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        passed = result.returncode == 0
        message = "Python syntax validation passed" if passed else f"Syntax errors: {result.stderr}"
        return GateStep("Syntax Validation", passed, message)
    except Exception as e:
        return GateStep("Syntax Validation", False, f"Error running syntax check: {e}")


def validate_imports() -> GateStep:
    """Validate that all imports can be resolved."""
    try:
        # Simple import validation - try importing key modules
        import_checks = [
            "src.analytics.browser_automation_pilot",
            "src.analytics.darts",
            "src.market_intelligence.ai_credit_stress_signal"
        ]
        
        for module in import_checks:
            try:
                __import__(module)
            except ImportError as e:
                return GateStep("Import Validation", False, f"Import error in {module}: {e}")
        
        return GateStep("Import Validation", True, "All imports validated successfully")
    except Exception as e:
        return GateStep("Import Validation", False, f"Error validating imports: {e}")


def validate_dependencies() -> GateStep:
    """Validate that required dependencies are available."""
    try:
        required_deps = ['pandas', 'numpy', 'requests']
        for dep in required_deps:
            try:
                __import__(dep)
            except ImportError:
                return GateStep("Dependencies", False, f"Missing required dependency: {dep}")
        
        return GateStep("Dependencies", True, "All dependencies available")
    except Exception as e:
        return GateStep("Dependencies", False, f"Error checking dependencies: {e}")


def run_quality_gates() -> GateReport:
    """Run all quality gates and return a report."""
    steps = []
    steps.append(validate_syntax())
    steps.append(validate_imports())
    steps.append(validate_dependencies())

    overall_passed = all(step.passed for step in steps)
    summary = "All gates passed" if overall_passed else "Some gates failed"
    
    return GateReport(steps, overall_passed, summary)


def render_report(report: GateReport) -> str:
    """Render a quality gate report as markdown."""
    lines = ["# Quality Gate Report", ""]

    for step in report.steps:
        status = "✅" if step.passed else "❌"
        lines.append(f"## {status} {step.name}")
        lines.append(f"{step.message}")
        lines.append("")

    lines.append("## Summary")
    lines.append(f"Overall Status: {'✅ PASSED' if report.overall_passed else '❌ FAILED'}")
    lines.append(f"{report.summary}")

    return "\n".join(lines)