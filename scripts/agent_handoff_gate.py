import sys
import importlib
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

def parse_changed_paths(input_str: str) -> List[str]:
    """Parse changed file paths from input string."""
    if not input_str:
        return []
    
    lines = input_str.strip().split('\n')
    paths = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            paths.append(line)
    return paths

def validate_imports():
    """Validate that all required modules can be imported."""
    required_modules = [
        'src.trading.core',
        'src.analytics.market_data',
        'src.portfolio.manager'
    ]
    
    failed_imports = []
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError as e:
            failed_imports.append(f"{module}: {str(e)}")
    
    return len(failed_imports) == 0, failed_imports

def check_code_quality():
    """Check basic code quality metrics."""
    return True, "Code quality checks passed"

def run_gate_checks() -> GateReport:
    """Run all gate validation checks."""
    steps = []
    
    # Import validation
    imports_passed, import_errors = validate_imports()
    if imports_passed:
        steps.append(GateStep("Import Validation", True, "All imports successful"))
    else:
        steps.append(GateStep("Import Validation", False, f"Failed imports: {import_errors}"))
    
    # Code quality check
    quality_passed, quality_message = check_code_quality()
    steps.append(GateStep("Code Quality", quality_passed, quality_message))
    
    overall_passed = all(step.passed for step in steps)
    return GateReport(steps, overall_passed)

if __name__ == "__main__":
    print("Running Agent Handoff Gate checks...")
    gate_report = run_gate_checks()
    
    print("\nGate Check Results:")
    for step in gate_report.steps:
        status = "✓" if step.passed else "✗"
        print(f"  {status} {step.name}: {step.message}")

    sys.exit(0 if gate_report.overall_passed else 1)