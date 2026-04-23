import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class ContextBundle:
    """Bundle of context information for agent workflows."""
    project_summary: str
    recent_changes: List[str]
    active_issues: List[str]
    key_files: List[str]
    dependencies: List[str]
    metadata: Dict[str, Any]


def build_context_bundle(
    focus_areas: Optional[List[str]] = None,
    include_git_history: bool = True
) -> ContextBundle:
    """Build a comprehensive context bundle for agent workflows."""
    
    # Project summary
    readme_path = REPO_ROOT / "README.md"
    project_summary = ""
    if readme_path.exists():
        with open(readme_path, 'r') as f:
            lines = f.readlines()
            # Take first 10 lines as summary
            project_summary = ''.join(lines[:10]).strip()
    
    # Recent changes
    recent_changes = []
    if include_git_history:
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT
            )
            if result.returncode == 0:
                recent_changes = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        except Exception:
            pass
    
    # Active issues (mock for now)
    active_issues = []
    
    # Key files
    key_files = []
    important_patterns = [
        "src/trading/*.py",
        "src/safety/*.py",
        "config/*.yaml",
        "requirements.txt",
        "setup.py"
    ]
    
    for pattern in important_patterns:
        if '*' in pattern:
            import glob
            key_files.extend(glob.glob(str(REPO_ROOT / pattern)))
        else:
            file_path = REPO_ROOT / pattern
            if file_path.exists():
                key_files.append(str(file_path))
    
    # Dependencies
    dependencies = []
    req_files = [
        REPO_ROOT / "requirements.txt",
        REPO_ROOT / "setup.py",
        REPO_ROOT / "pyproject.toml"
    ]
    
    for req_file in req_files:
        if req_file.exists() and req_file.name == "requirements.txt":
            with open(req_file, 'r') as f:
                dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            break
    
    # Metadata
    metadata = {
        "repo_root": str(REPO_ROOT),
        "focus_areas": focus_areas or [],
        "generated_at": str(Path(__file__).stat().st_mtime),
        "total_files": len(key_files)
    }
    
    return ContextBundle(
        project_summary=project_summary,
        recent_changes=recent_changes,
        active_issues=active_issues,
        key_files=key_files,
        dependencies=dependencies,
        metadata=metadata
    )


def save_context_bundle(bundle: ContextBundle, output_path: str) -> None:
    """Save context bundle to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(asdict(bundle), f, indent=2)


def load_context_bundle(input_path: str) -> ContextBundle:
    """Load context bundle from JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    return ContextBundle(**data)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Workflow Toolkit")
    parser.add_argument("--output", "-o", help="Output file for context bundle")
    parser.add_argument("--focus", nargs="*", help="Focus areas for context")
    parser.add_argument("--no-git", action="store_true", help="Skip git history")
    
    args = parser.parse_args()
    
    bundle = build_context_bundle(
        focus_areas=args.focus,
        include_git_history=not args.no_git
    )
    
    if args.output:
        save_context_bundle(bundle, args.output)
        print(f"Context bundle saved to {args.output}")
    else:
        print(json.dumps(asdict(bundle), indent=2))


if __name__ == "__main__":
    main()