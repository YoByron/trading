# Cloud Run Jobs Migration Plan

**Status**: Draft | **Owner**: Trading CTO | **Date**: 2025-12-13

## 1. Executive Summary
The current trading system runs as a monolithic `systemd` service (`trading-system.service`) executing `src/main.py`, which maintains an internal Loop with `schedule` library.
To align with Antigravity best practices, we will migrate to **Cloud Run Jobs** triggered by **Cloud Scheduler**. This removes the need for a 24/7 server, improves observability, and isolates failures.

## 2. Current Architecture (Monolith)
* **Runtime**: VM / Always-on Container
* **Entry Point**: `src/main.py` (Infinite Loop)
* **Scheduling**: Internal Python `schedule` library
* **Process**: Single long-running process
* **Risk**: If the process crashes, all schedules are lost until restart. Memory leaks accumulate.

## 3. Target Architecture (Serverless)
* **Runtime**: Google Cloud Run Jobs
* **Entry Point**: `scripts/autonomous_trader.py` (Single-shot execution)
* **Scheduling**: Google Cloud Scheduler (Cron)
* **Process**: Ephemeral containers (Start -> Trade -> Die)
* **Benefits**: Perfect isolation, zero maintenance, pay-per-use, native retries.

## 4. Migration Steps

### Phase 1: Refactor Entry Points
The current `src/main.py` mixes scheduling and execution. We need strict separation.
* [ ] **Action**: Verify `scripts/autonomous_trader.py` can run a *single* strategy pass and exit.
    * Flag: `--strategy core`
    * Flag: `--strategy growth`
    * Flag: `--task risk-reset`
* [ ] **Action**: Ensure `src/orchestrator/main.py` (Hybrid Funnel) supports "Run Once" mode.

### Phase 2: Docker Container Update
Ensure the container handles CLI arguments correctly for job execution.
* [ ] **Action**: Update `Dockerfile` ENTRYPOINT to allow passing args.
    * Current: `CMD ["python", ...]` (Fixed)
    * Target: `ENTRYPOINT ["python", "scripts/autonomous_trader.py"]`

### Phase 3: Job Definitions (Terraform/gcloud)
Define the jobs mapping to current internal schedule.

| Job Name | Schedule (ET) | Command |
|----------|---------------|---------|
| `trade-risk-reset` | 09:30 Daily | `--task risk-reset` |
| `trade-core` | 10:00 Daily | `--strategy core` |
| `trade-growth` | 09:35 Mon | `--strategy growth` |
| `trade-ipo-check` | 10:00 Wed | `--strategy ipo` |
| `trade-eod-report` | 16:30 Daily | `--task eod-report` |

### Phase 4: Observability
* [ ] **Logging**: Ensure structured JSON logging to stdout (Cloud Logging picks this up).
* [ ] **Alerting**: Cloud Monitoring alert on "Job Failed" metric.

## 5. Verification Plan
1. **Local Test**: `docker run trading-image --strategy core --dry-run`
2. **Cloud Test**: Deploy manual Job, trigger via GUI, check logs.
3. **Shadow Mode**: Run Cloud Run Jobs in `--paper` mode alongside production systemd.

## 6. Rollout
1. Deploy Cloud Run Jobs (Paper Mode).
2. Verify 1 week of execution.
3. Stop `systemd` service.
4. Promote Jobs to Live Mode.
