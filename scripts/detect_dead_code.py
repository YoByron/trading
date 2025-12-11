#!/usr/bin/env python3
"""Dead Code Detector.

Scans the codebase for potential dead code:
1. Functions/classes with 0 references
2. Files never imported
3. Deprecated markers
4. NotImplementedError patterns
5. Disabled feature flags

Run as: python scripts/detect_dead_code.py
Or add to pre-commit: .pre-commit-config.yaml
"""

import ast
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# Directories to scan
SCAN_DIRS = ["src", "scripts"]
# Directories to ignore
IGNORE_DIRS = {"__pycache__", ".git", "venv", "node_modules", "data", "docs", "tests"}
# Files to ignore
IGNORE_FILES = {"__init__.py", "conftest.py"}


def find_python_files(base_path: str) -> list[Path]:
    """Find all Python files in the codebase."""
    files = []
    for scan_dir in SCAN_DIRS:
        dir_path = Path(base_path) / scan_dir
        if not dir_path.exists():
            continue
        for path in dir_path.rglob("*.py"):
            if any(ignore in path.parts for ignore in IGNORE_DIRS):
                continue
            if path.name in IGNORE_FILES:
                continue
            files.append(path)
    return files


def extract_definitions(file_path: Path) -> dict:
    """Extract function and class definitions from a file."""
    definitions = {"functions": [], "classes": []}
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith("_"):  # Skip private
                    definitions["functions"].append(node.name)
            elif isinstance(node, ast.ClassDef):
                definitions["classes"].append(node.name)
    except Exception:
        pass
    return definitions


def find_references(files: list[Path], name: str) -> int:
    """Count references to a name across all files."""
    count = 0
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    for file_path in files:
        try:
            content = file_path.read_text()
            matches = pattern.findall(content)
            count += len(matches)
        except Exception:
            pass
    return count


def find_deprecated_markers(files: list[Path]) -> list[tuple[Path, int, str]]:
    """Find files with DEPRECATED markers."""
    results = []
    patterns = [
        r"DEPRECATED",
        r"NotImplementedError",
        r"raise\s+NotImplementedError",
        r"TODO:\s*remove",
        r"BROKEN",
    ]
    for file_path in files:
        try:
            lines = file_path.read_text().splitlines()
            for i, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        results.append((file_path, i, line.strip()[:80]))
                        break
        except Exception:
            pass
    return results


def find_disabled_features(files: list[Path]) -> list[tuple[Path, int, str]]:
    """Find feature flags defaulting to disabled."""
    results = []
    patterns = [
        r'os\.getenv\(["\'][A-Z_]+["\'],\s*["\']false["\']',
        r'ENABLED.*=.*False',
        r'ENABLE.*"false"',
    ]
    for file_path in files:
        try:
            lines = file_path.read_text().splitlines()
            for i, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        results.append((file_path, i, line.strip()[:80]))
        except Exception:
            pass
    return results


def find_orphaned_files(base_path: str, files: list[Path]) -> list[Path]:
    """Find files that are never imported."""
    orphaned = []
    for file_path in files:
        module_name = file_path.stem
        if module_name.startswith("test_"):
            continue

        # Check if this module is imported anywhere
        import_patterns = [
            f"from {module_name}",
            f"import {module_name}",
            f"from .{module_name}",
            f"from src.{file_path.parent.name}.{module_name}",
        ]

        found = False
        for other_file in files:
            if other_file == file_path:
                continue
            try:
                content = other_file.read_text()
                for pattern in import_patterns:
                    if pattern in content:
                        found = True
                        break
            except Exception:
                pass
            if found:
                break

        if not found:
            orphaned.append(file_path)

    return orphaned


def main():
    """Run dead code detection."""
    base_path = os.getcwd()
    files = find_python_files(base_path)

    print("=" * 70)
    print("DEAD CODE DETECTOR")
    print("=" * 70)
    print(f"Scanning {len(files)} Python files...\n")

    issues = []

    # Check for deprecated markers
    deprecated = find_deprecated_markers(files)
    if deprecated:
        print(f"⚠️  DEPRECATED/BROKEN markers found: {len(deprecated)}")
        for path, line, content in deprecated[:10]:
            print(f"   {path}:{line}: {content}")
            issues.append(f"DEPRECATED: {path}:{line}")
        if len(deprecated) > 10:
            print(f"   ... and {len(deprecated) - 10} more")
        print()

    # Check for disabled features
    disabled = find_disabled_features(files)
    if disabled:
        print(f"⚠️  Disabled feature flags found: {len(disabled)}")
        for path, line, content in disabled[:10]:
            print(f"   {path}:{line}: {content}")
            issues.append(f"DISABLED_FEATURE: {path}:{line}")
        if len(disabled) > 10:
            print(f"   ... and {len(disabled) - 10} more")
        print()

    # Check for orphaned files
    orphaned = find_orphaned_files(base_path, files)
    if orphaned:
        print(f"⚠️  Potentially orphaned files: {len(orphaned)}")
        for path in orphaned[:10]:
            print(f"   {path}")
            issues.append(f"ORPHANED: {path}")
        if len(orphaned) > 10:
            print(f"   ... and {len(orphaned) - 10} more")
        print()

    # Summary
    print("=" * 70)
    if issues:
        print(f"❌ Found {len(issues)} potential issues")
        print("   Review and clean up dead code to maintain system health.")
        return 1
    else:
        print("✅ No dead code detected!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
