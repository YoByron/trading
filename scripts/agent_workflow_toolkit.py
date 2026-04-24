from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json
import os

@dataclass
class ContextBundle:
    project_info: Dict[str, Any]
    current_state: Dict[str, Any]
    recent_changes: List[Dict[str, Any]]
    key_files: List[str]
    dependencies: List[str]

def build_context_bundle(project_path: str = ".") -> ContextBundle:
    """Build a comprehensive context bundle for agent handoff"""
    
    # Get project info
    project_info = {
        "name": os.path.basename(os.path.abspath(project_path)),
        "path": os.path.abspath(project_path),
        "structure": _get_project_structure(project_path)
    }
    
    # Get current state
    current_state = {
        "git_branch": _get_git_branch(project_path),
        "last_commit": _get_last_commit(project_path),
        "modified_files": _get_modified_files(project_path)
    }
    
    # Get recent changes (simplified)
    recent_changes = _get_recent_changes(project_path)
    
    # Identify key files
    key_files = _identify_key_files(project_path)
    
    # Get dependencies
    dependencies = _get_dependencies(project_path)
    
    return ContextBundle(
        project_info=project_info,
        current_state=current_state, 
        recent_changes=recent_changes,
        key_files=key_files,
        dependencies=dependencies
    )

def _get_project_structure(project_path: str) -> Dict[str, Any]:
    """Get basic project structure"""
    structure = {}
    try:
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            rel_root = os.path.relpath(root, project_path)
            if rel_root == '.':
                rel_root = 'root'
            
            structure[rel_root] = files[:10]  # Limit to first 10 files
    except Exception:
        structure = {"error": "Could not read project structure"}
    
    return structure

def _get_git_branch(project_path: str) -> str:
    """Get current git branch"""
    try:
        import subprocess
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd=project_path)
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"

def _get_last_commit(project_path: str) -> str:
    """Get last commit info"""
    try:
        import subprocess
        result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                              capture_output=True, text=True, cwd=project_path)
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"

def _get_modified_files(project_path: str) -> List[str]:
    """Get list of modified files"""
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd=project_path)
        if result.returncode == 0:
            return [line.strip()[3:] for line in result.stdout.split('\n') if line.strip()]
        return []
    except Exception:
        return []

def _get_recent_changes(project_path: str) -> List[Dict[str, Any]]:
    """Get recent changes (simplified)"""
    try:
        import subprocess
        result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                              capture_output=True, text=True, cwd=project_path)
        if result.returncode == 0:
            changes = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    changes.append({"commit": line.strip()})
            return changes
        return []
    except Exception:
        return []

def _identify_key_files(project_path: str) -> List[str]:
    """Identify key files in the project"""
    key_patterns = [
        'requirements.txt', 'setup.py', 'pyproject.toml',
        'README.md', 'README.rst',
        'main.py', 'app.py', '__init__.py'
    ]
    
    key_files = []
    try:
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file in key_patterns or file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), project_path)
                    key_files.append(rel_path)
                    if len(key_files) >= 20:  # Limit results
                        break
    except Exception:
        pass
    
    return key_files

def _get_dependencies(project_path: str) -> List[str]:
    """Get project dependencies"""
    dependencies = []
    
    # Check requirements.txt
    req_file = os.path.join(project_path, 'requirements.txt')
    if os.path.exists(req_file):
        try:
            with open(req_file, 'r') as f:
                dependencies.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
        except Exception:
            pass
    
    # Check pyproject.toml
    pyproject_file = os.path.join(project_path, 'pyproject.toml')
    if os.path.exists(pyproject_file):
        dependencies.append("pyproject.toml dependencies found")
    
    return dependencies

def save_context_bundle(bundle: ContextBundle, output_path: str):
    """Save context bundle to file"""
    try:
        with open(output_path, 'w') as f:
            json.dump({
                'project_info': bundle.project_info,
                'current_state': bundle.current_state,
                'recent_changes': bundle.recent_changes,
                'key_files': bundle.key_files,
                'dependencies': bundle.dependencies
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving context bundle: {e}")

def load_context_bundle(input_path: str) -> Optional[ContextBundle]:
    """Load context bundle from file"""
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
            return ContextBundle(
                project_info=data['project_info'],
                current_state=data['current_state'],
                recent_changes=data['recent_changes'],
                key_files=data['key_files'],
                dependencies=data['dependencies']
            )
    except Exception as e:
        print(f"Error loading context bundle: {e}")
        return None

if __name__ == "__main__":
    bundle = build_context_bundle()
    print("=== PROJECT CONTEXT BUNDLE ===")
    print(f"Project: {bundle.project_info['name']}")
    print(f"Branch: {bundle.current_state['git_branch']}")
    print(f"Last commit: {bundle.current_state['last_commit']}")
    print(f"Key files: {len(bundle.key_files)}")
    print(f"Dependencies: {len(bundle.dependencies)}")