from typing import List, NamedTuple
import re

class GateStepResult(NamedTuple):
    """Result of a gate step evaluation."""
    risk_level: str
    changed_files: List[str]
    recommendations: List[str]

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
        # Handle git diff --name-only output
        if line.strip():
            changed_files.append(line.strip())

    return changed_files

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
        r'src/core/',
        r'src/trading/',
        r'requirements\.txt',
        r'setup\.py',
        r'pyproject\.toml'
    ]
    
    medium_risk_patterns = [
        r'src/',
        r'tests/',
        r'\.py$'
    ]
    
    for file_path in changed_files:
        # Check for high risk changes
        for pattern in high_risk_patterns:
            if re.search(pattern, file_path):
                risk_level = "HIGH"
                recommendations.append(f"High-risk file changed: {file_path}")
                break
        
        # Check for medium risk changes if not already high risk
        if risk_level != "HIGH":
            for pattern in medium_risk_patterns:
                if re.search(pattern, file_path):
                    risk_level = "MEDIUM"
                    break
    
    if risk_level == "HIGH":
        recommendations.append("Consider thorough testing before handoff")
        recommendations.append("Review core system changes carefully")
    elif risk_level == "MEDIUM":
        recommendations.append("Run basic test suite before handoff")
    
    return GateStepResult(
        risk_level=risk_level,
        changed_files=changed_files,
        recommendations=recommendations
    )

def main():
    """Main entry point for agent handoff gate."""
    import subprocess

    try:
        # Get changed files from git
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            check=True
        )

        changed_files = parse_changed_paths(result.stdout)
        report = assess_handoff_risk(changed_files)

        print(f"Risk Level: {report.risk_level}")
        print(f"Changed Files: {len(report.changed_files)}")

        if report.recommendations:
            print("Recommendations:")
            for rec in report.recommendations:
                print(f"  - {rec}")
        
        # Exit with non-zero code for high risk
        if report.risk_level == "HIGH":
            exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()