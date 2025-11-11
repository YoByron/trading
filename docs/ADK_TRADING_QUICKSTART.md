# ADK Trading Orchestrator Quickstart

This guide describes how to run the Go-based ADK orchestrator introduced in `go/adk_trading` and how to consume it from the Python trading stack.

## Prerequisites

- Go 1.24.4 or newer (`go version`).
- A valid `GOOGLE_API_KEY` with access to Gemini 2.5 models.
- Existing trading dataset under `data/` (historical OHLCV CSV files are already pull-through by the repo).

## Launch the ADK service

```bash
# from repository root
export GOOGLE_API_KEY="your-key"
./scripts/run_adk_trading_service.sh
```

The launcher will start the ADK universal server on `http://127.0.0.1:8080`. The REST API is exposed under `/api`. Logs are appended to `logs/adk_orchestrator.jsonl`.

## Invoke from Python

```python
from src.orchestration.adk_client import ADKOrchestratorClient

client = ADKOrchestratorClient()
result = client.run(
    symbol="NVDA",
    context={"mode": "paper", "notes": "evening risk check"},
)

print(result.final_text)

# Parse the structured JSON payload (raises if invalid JSON).
structured = client.run_structured(
    symbol="NVDA",
    context={"mode": "paper", "notes": "evening risk check"},
)
print(structured["trade_summary"])
```

The client automatically provisions sessions and returns the final JSON summary emitted by the root ADK agent alongside the raw event stream.

## Operational notes

- The Go orchestrator reads historical data from `data/historical` and writes audit events to `logs/adk_orchestrator.jsonl`.
- Risk approvals use the built-in `risk_budget_check` tool. Tune defaults via the `--app`, `--data_dir`, and `--log_path` flags or environment variables:
  - `ADK_MODEL`
  - `ADK_DATA_DIR`
  - `ADK_LOG_PATH`
- To expose the API on a different port, set `ADK_PORT` before running the launcher, e.g. `ADK_PORT=8090 ./scripts/run_adk_trading_service.sh`.
- For cross-origin access, configure `ADK_WEBUI_ORIGIN` to set the API CORS allow-list (defaults to `localhost:8080`).


