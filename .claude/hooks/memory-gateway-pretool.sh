#!/usr/bin/env bash
# Run low-noise ThumbGate gate checks using the repo's custom high-risk gates.

set -euo pipefail

TOOL_COMMAND="${1-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
CUSTOM_GATES="${PROJECT_ROOT}/config/memory-gateway/gates.json"
cd "${PROJECT_ROOT}"

PATH_EXPORTS="$(
	python3 - "${PROJECT_ROOT}" "${CUSTOM_GATES}" <<'PY'
import json
import sys
from pathlib import Path

from src.learning.memory_gateway_feedback import resolve_thumbgate_paths

project_root = Path(sys.argv[1]).resolve()
custom_gates = Path(sys.argv[2]).resolve()
paths = resolve_thumbgate_paths(project_root)
print(json.dumps({
    "feedback_dir": str(paths.feedback_dir),
    "legacy_feedback_dir": str(paths.legacy_feedback_dir),
    "custom_gates": str(custom_gates),
}))
PY
)" || true

if [[ -n ${PATH_EXPORTS} ]]; then
	THUMBGATE_FEEDBACK_DIR="$(printf '%s' "${PATH_EXPORTS}" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["feedback_dir"])')"
	THUMBGATE_LEGACY_FEEDBACK_DIR="$(printf '%s' "${PATH_EXPORTS}" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["legacy_feedback_dir"])')"
	THUMBGATE_GATES_CONFIG="$(printf '%s' "${PATH_EXPORTS}" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["custom_gates"])')"
else
	THUMBGATE_FEEDBACK_DIR="${PROJECT_ROOT}/.thumbgate"
	THUMBGATE_LEGACY_FEEDBACK_DIR="${PROJECT_ROOT}/.rlhf"
	THUMBGATE_GATES_CONFIG="${CUSTOM_GATES}"
fi
export THUMBGATE_PROJECT_DIR="${PROJECT_ROOT}"
export THUMBGATE_FEEDBACK_DIR
export THUMBGATE_LEGACY_FEEDBACK_DIR
export THUMBGATE_GATES_CONFIG

HOOK_JSON="$(
	python3 - "${TOOL_COMMAND}" <<'PY'
import json
import sys

command = sys.argv[1] if len(sys.argv) > 1 else ""
print(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
PY
)"

RESULT="$(printf '%s' "${HOOK_JSON}" | npx -y thumbgate@0.9.14 gate-check 2>/dev/null || true)"

if [[ -z ${RESULT} || ${RESULT} == "{}" ]]; then
	exit 0
fi

printf '%s\n' "${RESULT}"

if printf '%s' "${RESULT}" | grep -q '"permissionDecision"[[:space:]]*:[[:space:]]*"deny"'; then
	exit 2
fi

exit 0
