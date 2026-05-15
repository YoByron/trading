# Prevention Rules

Generated from negative feedback memories (time-weighted, half-life: 7d).

## general
- Recurrence count: 9 (weighted: 1.9)
- Rule: For trading/North Star status, lead with hard truth and exact next actions: freeze scale, define kill criteria, audit current open risk, verify latest broker state, and implement/trigger automations instead of abstract conditional statements.
- Latest mistake: MISTAKE: The response sounded evasive/confused to the user and did not give a decisive right-now operating plan with concrete...

## Root Cause Categories
- guardrail_triggered: 3 failures

## Repeated Failure Constraints
- security:generic_assignment: 4 failures
- security:github_pat: 2 failures

## Auto-Review & Sandboxing Rules (Reviewer Agent)
- **Constraint:** `sandboxing:writable_roots` - Block any write action outside of `src/`, `tests/`, `data/`, `.claude/`, `scripts/`, or `.thumbgate/`.
- **Constraint:** `security:credential_protection` - Block any action reading or modifying `.env` or secret-carrying files.
- **Constraint:** `safety:ledger_backup` - Modifications to `data/system_state.json` or `data/trades.json` MUST be preceded by a backup in `data/backups/`.
- **Constraint:** `safety:circuit_breaker` - After 3 consecutive safety rejections, the agent must halt and request human intervention.
