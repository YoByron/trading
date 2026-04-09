#!/usr/bin/env python3
"""Thin CLI wrapper for hook feedback capture via ThumbGate."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def process_user_message(
    user_message: str,
    *,
    project_root: Path,
    runner: Any = None,
) -> dict[str, Any]:
    from src.learning.memory_gateway_feedback import (
        append_feedback_fallback,
        build_feedback_context,
        command_return_code,
        detect_feedback_signal,
        extract_last_assistant_response,
        normalize_text,
        resolve_thumbgate_paths,
        run_command,
        thumbgate_capture_command,
        thumbgate_env,
        thumbgate_rules_command,
    )

    if runner is None:
        runner = run_command

    normalized_message = normalize_text(user_message, limit=1000)
    signal = detect_feedback_signal(normalized_message)
    if signal is None:
        return {"status": "ignored", "reason": "no_feedback_signal"}

    assistant_response = extract_last_assistant_response()
    context, detail, improvement = build_feedback_context(
        signal,
        normalized_message,
        assistant_response,
    )

    capture_result = runner(
        thumbgate_capture_command(signal, context, detail, improvement),
        cwd=project_root,
        env=thumbgate_env(project_root),
    )
    accepted = command_return_code(capture_result) in {0, 2}

    fallback_path = None
    if not accepted:
        fallback_path = append_feedback_fallback(
            project_root=project_root,
            signal=signal,
            context=context,
            user_message=normalized_message,
            assistant_response=assistant_response,
        )

    prevention_rules = resolve_thumbgate_paths(project_root).prevention_rules
    rules_refreshed = False
    if accepted:
        rules_result = runner(
            thumbgate_rules_command(prevention_rules),
            cwd=project_root,
            env=thumbgate_env(project_root),
        )
        rules_refreshed = command_return_code(rules_result) == 0

    return {
        "status": "processed",
        "signal": signal.signal,
        "accepted": accepted,
        "fallback_log": str(fallback_path) if fallback_path else None,
        "rules_refreshed": rules_refreshed,
    }


def main() -> int:
    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
    user_message = sys.stdin.read()
    result = process_user_message(user_message, project_root=project_root)
    if result["status"] != "processed":
        return 0

    if result["signal"] == "thumbs_down":
        print("THUMBS DOWN DETECTED - recording via ThumbGate")
    elif result["signal"] == "thumbs_up":
        print("THUMBS UP DETECTED - recording via ThumbGate")

    if result["fallback_log"]:
        print(f"ThumbGate capture unavailable - wrote fallback log to {result['fallback_log']}")
    elif result["accepted"]:
        print("ThumbGate capture recorded")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
