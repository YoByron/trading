#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export GOOGLE_API_KEY="${GOOGLE_API_KEY:?GOOGLE_API_KEY must be set for ADK orchestrator}"

GO_DIR="${ROOT_DIR}/go/adk_trading"
LOG_PATH="${ROOT_DIR}/logs/adk_orchestrator.jsonl"
PORT="${ADK_PORT:-8080}"
WEBUI_ORIGIN="${ADK_WEBUI_ORIGIN:-localhost:8080}"

mkdir -p "$(dirname "${LOG_PATH}")"

cd "${GO_DIR}"
exec go run ./cmd/trading_orchestrator \
  --data_dir "${ROOT_DIR}/data" \
  --log_path "${LOG_PATH}" \
  --app "trading_orchestrator" \
  web --port "${PORT}" api --webui_address "${WEBUI_ORIGIN}"

