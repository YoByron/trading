import subprocess
import os
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
    overall_passed: bool
    recommendations: List[str]

def validate_tests():
    """Validate that tests are passing"""
    try:
        result = subprocess.run(['python', '-m', 'pytest', '-v'], capture_output=True, text=True)
        passed = result.returncode == 0
        message = "All tests passing" if passed else f"Tests failing: {result.stdout}"
        recommendations = [] if passed else ["Fix failing tests before proceeding"]
        return GateStep("Test Validation", passed, message, recommendations)
    except Exception as e:
        return GateStep("Test Validation", False, f"Error running tests: {str(e)}", ["Ensure pytest is installed and tests are runnable"])

def validate_lint():
    """Validate code quality with linting"""
    try:
        result = subprocess.run(['ruff', 'check', '.'], capture_output=True, text=True)
        passed = result.returncode == 0
        message = "Code quality checks passed" if passed else f"Linting issues found: {result.stdout}"
        recommendations = [] if passed else ["Fix linting issues before proceeding"]
        return GateStep("Lint Validation", passed, message, recommendations)
    except Exception as e:
        return GateStep("Lint Validation", False, f"Error running linter: {str(e)}", ["Ensure ruff is installed"])

def validate_dependencies():
    """Validate that all dependencies are properly installed"""
    try:
        import sys
        import pkg_resources
        
        # Check if we can import key modules
        required_modules = ['pandas', 'numpy', 'requests']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        passed = len(missing_modules) == 0
        message = "All dependencies available" if passed else f"Missing modules: {missing_modules}"
        recommendations = [] if passed else [f"Install missing dependencies: {', '.join(missing_modules)}"]
        
        return GateStep("Dependency Validation", passed, message, recommendations)
    except Exception as e:
        return GateStep("Dependency Validation", False, f"Error checking dependencies: {str(e)}", ["Check Python environment setup"])

def validate_environment():
    """Validate environment configuration"""
    try:
        # Check for basic environment setup
        issues = []
        
        # Check if we're in a reasonable working directory
        if not os.path.exists('src') and not os.path.exists('scripts'):
            issues.append("Not in project root directory")
        
        # Check for basic Python environment
        if not hasattr(sys, 'version_info') or sys.version_info < (3, 7):
            issues.append("Python version too old")
        
        passed = len(issues) == 0
        message = "Environment properly configured" if passed else f"Environment issues: {issues}"
        recommendations = [] if passed else ["Fix environment configuration issues"]
        
        return GateStep("Environment Validation", passed, message, recommendations)
    except Exception as e:
        return GateStep("Environment Validation", False, f"Error checking environment: {str(e)}", ["Check system configuration"])

def validate_security():
    """Basic security validation"""
    # Simple security check - look for common patterns
    security_issues = []

    # Check for hardcoded credentials (basic check)
    try:
        result = subprocess.run(['grep', '-r', 'password=', '.', '--exclude-dir=.git'],
                               capture_output=True, text=True)
        if result.stdout:
            security_issues.append("Potential hardcoded passwords found")
    except Exception:
        pass

    if security_issues:
        return GateStep(
            "Security Validation", 
            False, 
            f"Security issues found: {security_issues}", 
            ["Review and remove hardcoded credentials"]
        )
    else:
        return GateStep("Security Validation", True, "No obvious security issues", [])

def run_handoff_gate():
    """Run all validation steps for agent handoff"""
    steps = [
        validate_dependencies(),
        validate_environment(), 
        validate_tests(),
        validate_lint(),
        validate_security()
    ]

    # Collect all recommendations
    all_recommendations = []
    for step in steps:
        all_recommendations.extend(step.recommendations)

    # Determine overall result
    overall_passed = all(step.passed for step in steps)

    return GateStepResult(steps, overall_passed, all_recommendations)

if __name__ == "__main__":
    result = run_handoff_gate()
    
    print("=== AGENT HANDOFF GATE RESULTS ===")
    for step in result.steps:
        status = "✅ PASS" if step.passed else "❌ FAIL"
        print(f"{status} {step.name}: {step.message}")
        if step.recommendations:
            for rec in step.recommendations:
                print(f"  → {rec}")
    
    print(f"\nOverall Status: {'✅ READY FOR HANDOFF' if result.overall_passed else '❌ NOT READY'}")
    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f"  • {rec}")