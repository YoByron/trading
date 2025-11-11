# ADK Trading Deployment Playbook

This playbook covers the steps required to deploy and operate the Go-based ADK trading orchestrator in production.

## 1. Pre-flight Checklist

- [ ] `GOOGLE_API_KEY` configured with Gemini 2.5 access
- [ ] Alpaca keys stored in `.env` for Python orchestrator
- [ ] `data/historical` directory refreshed (last 24 hours)
- [ ] `rag_store` migrations applied (`python -m rag_store.sqlite_store`)
- [ ] CI pipeline green (`adk-ci` workflow)

## 2. Launch the ADK Service

```bash
export GOOGLE_API_KEY="***"
export ADK_PORT=8080
export ADK_WEBUI_ORIGIN="localhost:8080"
export ADK_HEALTH_ADDR=":8091"
./scripts/run_adk_trading_service.sh
```

## 3. Smoke Tests

1. **Health endpoint**
   ```bash
   curl -s http://127.0.0.1:8091/healthz | jq '.status'
   curl -s http://127.0.0.1:8091/metrics
   ```
2. **REST API**
   ```bash
   curl -s http://127.0.0.1:8080/api/list-apps
   ```
3. **Structured run**
   ```python
   from src.orchestration.adk_client import ADKOrchestratorClient
   client = ADKOrchestratorClient()
   print(client.run_structured("SPY"))
   ```

## 4. Python Orchestrator Cut-over

1. Update environment:
   ```bash
   export ADK_ENABLED=1
   export ADK_BASE_URL="http://127.0.0.1:8080/api"
   ```
2. Run `python src/main.py --mode paper --run-once --strategy core`
3. Verify log entries in `logs/adk_orchestrator.jsonl`
4. Confirm Alpaca order records and ADK summary in main log

## 5. Monitoring & Observability

- Scrape `/metrics` into Prometheus (or equivalent)
- Tail `logs/adk_orchestrator.jsonl` for the JSON audit trail
- Alerts:
  - No decision in 24h (`adk_decisions_total` stagnant)
  - Rising failure count (`adk_decisions_failures_total`)

## 6. Rollback Plan

1. Disable ADK usage:
   ```bash
   export ADK_ENABLED=0
   ```
2. Restart Python orchestrator (falls back to legacy strategy logic)
3. Stop the Go service (`Ctrl+C` in launch terminal)
4. Inspect latest log entries for failure cause

## 7. Post-Deployment Tasks

- Archive ADK health snapshots (`curl > logs/adk_health.json`)
- Record sentiment benchmarks from RAG store (`python scripts/report_sentiment.py`)
- Update dashboard widgets with ADK summary metrics

