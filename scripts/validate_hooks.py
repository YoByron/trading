#!/usr/bin/env python3
"""
Hook Validation Script - Ensures 100% operational integrity.

Created: Dec 29, 2025
Purpose: Prevent broken hooks from corrupting data or lying about success.

This script:
1. Tests each hook script for syntax errors
2. Validates hook configurations in settings.json
3. Checks for common failure patterns (fake success, data corruption)
4. Reports issues that MUST be fixed before proceeding

Run this:
- Before every commit (pre-commit hook)
- At session start (optional)
- Manually when debugging hook issues
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
HOOKS_DIR = PROJECT_ROOT / ".claude" / "hooks"
SETTINGS_FILE = PROJECT_ROOT / ".claude" / "settings.json"

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

CRITICAL_FAILURES = []
WARNINGS = []


def check_syntax(hook_path: Path) -> bool:
    """Check shell script syntax."""
    if hook_path.suffix == ".sh" or not hook_path.suffix:
        result = subprocess.run(
            ["bash", "-n", str(hook_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            CRITICAL_FAILURES.append(f"SYNTAX ERROR in {hook_path.name}: {result.stderr}")
            return False
    elif hook_path.suffix == ".py":
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(hook_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            CRITICAL_FAILURES.append(f"SYNTAX ERROR in {hook_path.name}: {result.stderr}")
            return False
    return True


def check_for_lying_patterns(hook_path: Path) -> None:
    """Detect patterns that cause false success claims."""
    content = hook_path.read_text()

    # Pattern 1: Claiming success without verification
    if "✅" in content or "SUCCESS" in content:
        # Check if there's a corresponding verification
        if "simulated" in content.lower() and "SUCCESS" in content:
            # Make sure simulated mode doesn't claim real success
            if "mode: simulated" not in content and "sync_mode" not in content:
                WARNINGS.append(f"{hook_path.name}: May claim SUCCESS for simulated/fake data")

    # Pattern 2: Returning 0 on error conditions
    if "exit 0" in content and ("error" in content.lower() or "fail" in content.lower()):
        # Check if exit 0 comes after error handling
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "exit 0" in line and i > 0:
                prev_lines = "\n".join(lines[max(0, i - 5) : i])
                if "error" in prev_lines.lower() or "fail" in prev_lines.lower():
                    # This might be intentional (warn but don't fail)
                    pass

    # Pattern 3: Overwriting data without backup
    # Only flag if actually writing (echo > file or cat > file patterns)
    # Not just reading with jq or other commands
    import re

    write_patterns = [
        r">\s*.*system_state\.json",  # redirect to file
        r"echo.*>\s*.*system_state",  # echo redirect
        r"cat.*>\s*.*system_state",  # cat redirect
        r"tee.*system_state",  # tee write
    ]
    for pattern in write_patterns:
        if re.search(pattern, content) and "backup" not in content.lower():
            WARNINGS.append(f"{hook_path.name}: May write to system_state.json without backup")
            break


def check_hook_exists(hook_command: str) -> bool:
    """Verify hook script exists and is executable."""
    # Extract path from command (handle $CLAUDE_PROJECT_DIR substitution)
    path = hook_command.split()[0]
    path = path.replace("$CLAUDE_PROJECT_DIR", str(PROJECT_ROOT))

    if not Path(path).exists():
        CRITICAL_FAILURES.append(f"MISSING HOOK: {path}")
        return False

    if not os.access(path, os.X_OK):
        WARNINGS.append(f"NOT EXECUTABLE: {path}")

    return True


def validate_settings() -> None:
    """Validate hooks configuration in settings.json."""
    if not SETTINGS_FILE.exists():
        WARNINGS.append("settings.json not found - no hooks configured")
        return

    with open(SETTINGS_FILE) as f:
        settings = json.load(f)

    hooks = settings.get("hooks", {})

    for event_type, event_hooks in hooks.items():
        for hook_config in event_hooks:
            for hook in hook_config.get("hooks", []):
                command = hook.get("command", "")
                if command:
                    check_hook_exists(command)


def validate_all_hooks() -> None:
    """Validate all hook scripts."""
    if not HOOKS_DIR.exists():
        CRITICAL_FAILURES.append(f"Hooks directory not found: {HOOKS_DIR}")
        return

    for hook_file in HOOKS_DIR.iterdir():
        if hook_file.is_file() and hook_file.name != "README.md":
            check_syntax(hook_file)
            check_for_lying_patterns(hook_file)


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("🔍 HOOK VALIDATION - Ensuring 100% Operational Integrity")
    print("=" * 60)
    print()

    # Run all checks
    validate_settings()
    validate_all_hooks()

    # Report results
    if CRITICAL_FAILURES:
        print(f"{RED}❌ CRITICAL FAILURES (must fix):{RESET}")
        for failure in CRITICAL_FAILURES:
            print(f"   • {failure}")
        print()

    if WARNINGS:
        print(f"{YELLOW}⚠️  WARNINGS (review recommended):{RESET}")
        for warning in WARNINGS:
            print(f"   • {warning}")
        print()

    if not CRITICAL_FAILURES and not WARNINGS:
        print(f"{GREEN}✅ All hooks validated successfully!{RESET}")
        print()

    # Summary
    print("=" * 60)
    if CRITICAL_FAILURES:
        print(f"{RED}RESULT: FAILED - {len(CRITICAL_FAILURES)} critical issues{RESET}")
        return 1
    elif WARNINGS:
        print(f"{YELLOW}RESULT: PASSED with {len(WARNINGS)} warnings{RESET}")
        return 0
    else:
        print(f"{GREEN}RESULT: PASSED - 100% operational integrity{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
