#!/usr/bin/env python3
"""
Update session state for RLHF action tracking.

Called after significant actions to record what Claude did.
The feedback hook reads this to provide meaningful learning context.

Usage:
    python update_session_state.py --action "Fixed bug" --tool "Edit" --files "src/main.py" --summary "Repaired null check"

    # Or pipe from stdin for complex summaries:
    echo "Long summary here" | python update_session_state.py --action "Refactored" --tool "Write" --files "*.py"
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SESSION_STATE_FILE = Path(__file__).parent.parent.parent.parent / "data" / "feedback" / "session_state.json"


def update_session_state(action: str, tool: str, files: str, summary: str = None):
    """Update session state with last action details."""
    SESSION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Read summary from stdin if not provided
    if summary is None and not sys.stdin.isatty():
        summary = sys.stdin.read().strip()[:500]

    state = {
        "last_action": action[:200] if action else "unknown",
        "last_tool": tool[:50] if tool else "unknown",
        "last_files": files[:300] if files else "",
        "last_summary": summary[:500] if summary else "",
        "timestamp": datetime.now().isoformat(),
    }

    # Load existing state to preserve history
    history = []
    if SESSION_STATE_FILE.exists():
        try:
            existing = json.loads(SESSION_STATE_FILE.read_text())
            history = existing.get("history", [])[-9:]  # Keep last 9
            # Add current state to history
            history.append({
                "action": existing.get("last_action"),
                "tool": existing.get("last_tool"),
                "timestamp": existing.get("timestamp"),
            })
        except (json.JSONDecodeError, KeyError):
            pass

    state["history"] = history

    SESSION_STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"📝 Session state updated: {action[:50]}...")
    return state


def main():
    parser = argparse.ArgumentParser(description="Update RLHF session state")
    parser.add_argument("--action", "-a", required=True, help="What action was performed")
    parser.add_argument("--tool", "-t", required=True, help="Which tool was used (Edit, Write, Bash, etc.)")
    parser.add_argument("--files", "-f", default="", help="Files affected (comma-separated)")
    parser.add_argument("--summary", "-s", default=None, help="Brief summary of what was done")

    args = parser.parse_args()
    update_session_state(args.action, args.tool, args.files, args.summary)


if __name__ == "__main__":
    main()
