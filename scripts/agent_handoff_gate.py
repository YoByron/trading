import os
import sys
import importlib
import subprocess
from dataclasses import dataclass
from typing import List

@dataclass
class GateStep:
    name: str
    passed: bool
    message: str

@dataclass
class GateReport:
    steps: List[GateStep]
    overall_passed: bool
    summary: str

@dataclass
class GateStepResult:
    step: GateStep
    details: str = ""

def validate_imports() -> GateStep:
    """Validate that all required modules can be imported."""
    try:
        import_checks = [
            "src.analytics.browser_automation_pilot",
            "src.analytics.ai_options_market_tracker",
            "src.market_intelligence.crypto_signal_processor",
            "src.market_intelligence.ai_credit_stress_signal"
        ]

        for module in import_checks:
            try:
                importlib.import_module(module)
            except ImportError as e:
                return GateStep("Import Validation", False, f"Import error in {module}: {e}")

        return GateStep("Import Validation", True, "All imports validated successfully")
    except Exception as e:
        return GateStep("Import Validation", False, f"Unexpected error: {e}")

def check_dependencies() -> GateStep:
    """Check that all required dependencies are available."""
    try:
        required_deps = [
            "pandas",
            "numpy",
            "requests",
            "selenium"
        ]

        for dep in required_deps:
            try:
                importlib.import_module(dep)
            except ImportError:
                return GateStep("Dependencies", False, f"Missing required dependency: {dep}")

        return GateStep("Dependencies", True, "All dependencies available")
    except Exception as e:
        return GateStep("Dependencies", False, f"Dependency check error: {e}")

def run_handoff_gate() -> GateReport:
    """Run all handoff gate checks."""
    steps = [
        validate_imports(),
        check_dependencies()
    ]

    overall_passed = all(step.passed for step in steps)
    summary = "All gates passed" if overall_passed else "Some gates failed"

    return GateReport(steps, overall_passed, summary)

if __name__ == "__main__":
    gate_report = run_handoff_gate()
    print(f"Gate Report: {gate_report.summary}")
    for step in gate_report.steps:
        status = "✓" if step.passed else "✗"
        print(f"  {status} {step.name}: {step.message}")
    
    sys.exit(0 if gate_report.overall_passed else 1)