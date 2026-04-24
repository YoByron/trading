import subprocess
import sys
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class GateStepResult:
    status: str
    risk_level: str
    recommendations: List[str]
    metadata: Dict[str, Any]

def get_changed_files_from_git() -> List[str]:
    """
    Get list of changed files from git diff
    
    Returns:
        List of file paths that have been changed
    """
    try:
        result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1'], 
                              capture_output=True, text=True)
        git_diff_output = result.stdout
    except Exception:
        return []
    
    changed_files = []
    lines = git_diff_output.strip().split('\n')

    for line in lines:
        if line.startswith('+++') or line.startswith('---'):
            continue
        else:
            parts = line.split()
            if parts:
                file_path = parts[-1]
                if file_path not in changed_files and not file_path.startswith('b/'):
                    changed_files.append(file_path)

    return changed_files

def assess_risk_level(changed_files: List[str]) -> GateStepResult:
    """
    Assess the risk level of changed files
    
    Args:
        changed_files: List of file paths that have been changed
        
    Returns:
        GateStepResult with risk assessment
    """

    risk_level = "LOW"
    recommendations = []
    
    high_risk_patterns = [
        "src/core/",
        "src/trading/",
        "requirements.txt",
        "pyproject.toml",
        "Dockerfile"
    ]
    
    medium_risk_patterns = [
        "src/",
        "tests/",
        "scripts/"
    ]
    
    for file_path in changed_files:
        for pattern in high_risk_patterns:
            if pattern in file_path:
                risk_level = "HIGH"
                recommendations.append(f"High-risk file changed: {file_path}")
                break

        if risk_level != "HIGH":
            for pattern in medium_risk_patterns:
                if pattern in file_path:
                    risk_level = "MEDIUM"
                    recommendations.append(f"Medium-risk file changed: {file_path}")
                    break

    if not recommendations:
        recommendations = ["Low risk changes detected"]

    return GateStepResult(
        status="ASSESSED",
        risk_level=risk_level,
        recommendations=recommendations,
        metadata={"changed_files": changed_files}
    )

def render_markdown_report(gate_result: GateStepResult) -> str:
    """
    Render a markdown report from gate result
    
    Args:
        gate_result: The gate step result to render
        
    Returns:
        Markdown formatted report string
    """
    report = f"# Gate Assessment Report\n\n"
    report += f"**Status:** {gate_result.status}\n"
    report += f"**Risk Level:** {gate_result.risk_level}\n\n"
    
    report += "## Recommendations\n\n"
    for rec in gate_result.recommendations:
        report += f"- {rec}\n"
    
    if gate_result.metadata.get("changed_files"):
        report += "\n## Changed Files\n\n"
        for file_path in gate_result.metadata["changed_files"]:
            report += f"- {file_path}\n"
    
    return report

def main():
    """Main function to run the agent handoff gate"""
    changed_files = get_changed_files_from_git()
    gate_result = assess_risk_level(changed_files)
    
    print("Agent Handoff Gate Assessment")
    print("=" * 30)
    print(f"Risk Level: {gate_result.risk_level}")
    print(f"Status: {gate_result.status}")
    print("\nRecommendations:")
    for rec in gate_result.recommendations:
        print(f"  - {rec}")
    
    if gate_result.risk_level == "HIGH":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()