import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class GateReport:
    risk_level: str
    recommendations: List[str]
    changed_files: List[str]

def parse_changed_paths(git_diff_output: str) -> List[str]:
    """Parse changed file paths from git diff output."""
    changed_files = []
    lines = git_diff_output.strip().split('\n')
    
    for line in lines:
        # Handle git diff --name-only output
        if line.strip():
            changed_files.append(line.strip())
    
    return changed_files

def assess_handoff_risk(changed_files: List[str]) -> GateReport:
    """Assess the risk level of changes for agent handoff."""
    risk_level = "low"
    recommendations = []

    # Check for high-risk file patterns
    high_risk_patterns = [
        "src/core/",
        "src/safety/",
        "config/trading.yaml"
    ]

    for file_path in changed_files:
        for pattern in high_risk_patterns:
            if pattern in file_path:
                risk_level = "high"
                recommendations.append(f"Review changes to critical file: {file_path}")
                break

    # Check for medium-risk patterns
    medium_risk_patterns = [
        "src/analytics/",
        "src/data/",
        "tests/"
    ]

    if risk_level != "high":
        for file_path in changed_files:
            for pattern in medium_risk_patterns:
                if pattern in file_path:
                    if risk_level != "high":
                        risk_level = "medium"
                    recommendations.append(f"Consider review of: {file_path}")
                    break

    return GateReport(
        risk_level=risk_level,
        recommendations=recommendations,
        changed_files=changed_files
    )

def main():
    """Main entry point for agent handoff gate."""
    import subprocess
    
    try:
        # Get changed files from git
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
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
                print(f"- {rec}")
                
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()