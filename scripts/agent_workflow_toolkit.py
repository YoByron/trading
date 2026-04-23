#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add project root to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class ContextBundle:
    """Bundle of context information for agent workflows"""
    files: Dict[str, str]
    metadata: Dict[str, Any]
    dependencies: List[str]
    workflow_type: str

def build_context_bundle(
    file_paths: List[str],
    workflow_type: str = "general",
    include_dependencies: bool = True
) -> ContextBundle:
    """Build a context bundle from file paths"""
    files = {}
    dependencies = []
    metadata = {
        "total_files": 0,
        "total_size": 0,
        "creation_time": None
    }
    
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists() and path.is_file():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                files[str(path)] = content
                metadata["total_size"] += len(content)
                
                # Extract dependencies if needed
                if include_dependencies and path.suffix == '.py':
                    deps = extract_python_dependencies(content)
                    dependencies.extend(deps)
            except Exception as e:
                files[str(path)] = f"Error reading file: {e}"
    
    metadata["total_files"] = len(files)
    dependencies = list(set(dependencies))  # Remove duplicates
    
    return ContextBundle(
        files=files,
        metadata=metadata,
        dependencies=dependencies,
        workflow_type=workflow_type
    )

def extract_python_dependencies(content: str) -> List[str]:
    """Extract Python import dependencies from file content"""
    dependencies = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('import ') or line.startswith('from '):
            dependencies.append(line)
    
    return dependencies

def analyze_workflow_complexity(bundle: ContextBundle) -> Dict[str, Any]:
    """Analyze the complexity of a workflow bundle"""
    analysis = {
        "file_count": bundle.metadata["total_files"],
        "total_size": bundle.metadata["total_size"],
        "dependency_count": len(bundle.dependencies),
        "complexity_score": 0,
        "risk_factors": []
    }
    
    # Calculate complexity score
    complexity_score = 0
    complexity_score += bundle.metadata["total_files"] * 2
    complexity_score += len(bundle.dependencies) * 3
    complexity_score += bundle.metadata["total_size"] // 1000
    
    analysis["complexity_score"] = complexity_score
    
    # Identify risk factors
    if bundle.metadata["total_files"] > 10:
        analysis["risk_factors"].append("High file count")
    
    if len(bundle.dependencies) > 20:
        analysis["risk_factors"].append("Many dependencies")
    
    if bundle.metadata["total_size"] > 100000:
        analysis["risk_factors"].append("Large codebase")
    
    return analysis

def generate_workflow_summary(bundle: ContextBundle) -> str:
    """Generate a text summary of the workflow bundle"""
    analysis = analyze_workflow_complexity(bundle)
    
    summary = f"""
Workflow Summary ({bundle.workflow_type}):
- Files: {analysis['file_count']}
- Dependencies: {analysis['dependency_count']}
- Total Size: {analysis['total_size']} characters
- Complexity Score: {analysis['complexity_score']}
"""
    
    if analysis["risk_factors"]:
        summary += f"\nRisk Factors:\n"
        for factor in analysis["risk_factors"]:
            summary += f"- {factor}\n"
    
    return summary

def main():
    """Main entry point for the workflow toolkit"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent workflow toolkit")
    parser.add_argument("--files", nargs='+', required=True, help="Files to include in bundle")
    parser.add_argument("--workflow-type", default="general", help="Type of workflow")
    parser.add_argument("--output", help="Output file for bundle")
    parser.add_argument("--summary", action="store_true", help="Generate summary only")
    
    args = parser.parse_args()
    
    # Build context bundle
    bundle = build_context_bundle(args.files, args.workflow_type)
    
    if args.summary:
        summary = generate_workflow_summary(bundle)
        print(summary)
    else:
        bundle_data = {
            "files": bundle.files,
            "metadata": bundle.metadata,
            "dependencies": bundle.dependencies,
            "workflow_type": bundle.workflow_type
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(bundle_data, f, indent=2)
        else:
            print(json.dumps(bundle_data, indent=2))

if __name__ == "__main__":
    main()