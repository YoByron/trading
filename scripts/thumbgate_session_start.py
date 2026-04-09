#!/usr/bin/env python3
"""Refresh ThumbGate session state and print a compact repo-specific summary."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from src.learning.memory_gateway_feedback import (
        command_return_code,
        render_session_start_report,
        run_command,
        thumbgate_env,
        thumbgate_session_start_command,
    )

    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
    result = run_command(
        thumbgate_session_start_command(),
        cwd=project_root,
        env=thumbgate_env(project_root),
        timeout=30,
    )
    if command_return_code(result) not in {0, 2}:
        stderr = (result.stderr or "").strip()
        if stderr:
            print(f"ThumbGate session refresh warning: {stderr}")

    print(render_session_start_report(project_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
