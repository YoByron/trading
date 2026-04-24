import os
import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class ContextBundle:
    """Bundle of context information for agent workflows"""
    project_info: Dict[str, Any]
    file_structure: Dict[str, Any]
    recent_changes: List[str]
    dependencies: List[str]
    environment_vars: Dict[str, str]

def get_project_structure(root_path: str = ".") -> Dict[str, Any]:
    """
    Get project file structure

    Args:
        root_path: Root directory to scan

    Returns:
        Dictionary representing project structure
    """
    structure = {}
    
    for root, dirs, files in os.walk(root_path):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        rel_root = os.path.relpath(root, root_path)
        if rel_root == '.':
            rel_root = ''
        
        current = structure
        if rel_root:
            parts = rel_root.split(os.sep)
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        for file in files:
            if not file.startswith('.') and not file.endswith('.pyc'):
                current[file] = 'file'
    
    return structure

def get_dependencies() -> List[str]:
    """
    Get project dependencies

    Returns:
        List of dependencies
    """
    dependencies = []
    
    # Check requirements.txt
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    dependencies.append(line)
    
    # Check pyproject.toml
    if os.path.exists('pyproject.toml'):
        try:
            import tomllib
            with open('pyproject.toml', 'rb') as f:
                data = tomllib.load(f)
                if 'project' in data and 'dependencies' in data['project']:
                    dependencies.extend(data['project']['dependencies'])
        except ImportError:
            pass
    
    return dependencies

def build_context_bundle(project_path: str = ".") -> ContextBundle:
    """
    Build a comprehensive context bundle for agent workflows

    Args:
        project_path: Path to the project root

    Returns:
        ContextBundle with project context
    """
    # Get project info
    project_info = {
        "name": os.path.basename(os.path.abspath(project_path)),
        "path": os.path.abspath(project_path),
        "python_files": [],
        "test_files": []
    }
    
    # Find Python and test files
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                rel_path = os.path.relpath(os.path.join(root, file), project_path)
                project_info["python_files"].append(rel_path)
                if 'test' in file or 'tests' in root:
                    project_info["test_files"].append(rel_path)
    
    # Get file structure
    file_structure = get_project_structure(project_path)
    
    # Get recent changes (placeholder)
    recent_changes = []
    
    # Get dependencies
    dependencies = get_dependencies()
    
    # Get environment variables
    environment_vars = dict(os.environ)
    
    return ContextBundle(
        project_info=project_info,
        file_structure=file_structure,
        recent_changes=recent_changes,
        dependencies=dependencies,
        environment_vars=environment_vars
    )