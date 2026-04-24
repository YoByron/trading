import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.safety.trading_policy_drift import (
    DEFAULT_POLICY_DOC_PATHS,
)

def parse_changed_paths(git_diff_output: str) -> List[str]:
    """Parse changed file paths from git diff output"""
    changed_paths = []
    for line in git_diff_output.split('\n'):
        if line.startswith('diff --git'):
            # Extract file path from diff line
            parts = line.split(' ')
            if len(parts) >= 4:
                path = parts[3][2:]  # Remove 'b/' prefix
                changed_paths.append(path)
    return changed_paths

@dataclass
class HandoffContext:
    """Context for agent handoff decisions"""
    changed_files: List[str]
    risk_level: str
    recommendations: List[str]

def evaluate_handoff_necessity(changed_files: List[str]) -> HandoffContext:
    """Evaluate if agent handoff is necessary based on changed files"""
    risk_level = "low"
    recommendations = []
    
    # Check for high-risk file patterns
    high_risk_patterns = [
        "src/trading/",
        "src/execution/",
        "src/risk/",
        "config/trading.yaml"
    ]
    
    for file_path in changed_files:
        for pattern in high_risk_patterns:
            if pattern in file_path:
                risk_level = "high"
                recommendations.append(f"Manual review required for {file_path}")
                break
    
    return HandoffContext(
        changed_files=changed_files,
        risk_level=risk_level,
        recommendations=recommendations
    )

def main():
    """Main function for agent handoff gate"""
    import subprocess
    
    # Get git diff
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True,
            text=True,
            check=True
        )
        changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        changed_files = []
    
    # Evaluate handoff necessity
    context = evaluate_handoff_necessity(changed_files)
    
    print(f"Risk Level: {context.risk_level}")
    if context.recommendations:
        print("Recommendations:", context.recommendations)

if __name__ == "__main__":
    main()