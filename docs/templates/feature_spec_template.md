# [Feature Name] - Feature Specification

**Status**: Draft | **Owner**: [Agent Name] | **Date**: [YYYY-MM-DD]

## 1. Goal & Context
* **Objective**: One-sentence summary of what this feature achieves.
* **Why**: Brief explanation of business value or technical necessity.
* **Success Metric**: How will we know it works? (e.g., "Passes new test suite", "Reduces latency by X%").

## 2. Technical Stack
* **Language**: Python 3.11+
* **Core Libraries**: [e.g. pandas, pydantic, alpaca-py]
* **New Dependencies**: [List any new packages or "None"]
* **Infrastructure**: [e.g. In-process agent, new cron job, simple function]

## 3. "Architect Mode" Constraints
* **Security**:
    * [ ] No secrets in code/logs
    * [ ] Validate all external inputs
* **Performance**:
    * [ ] No blocking main loop > 100ms
    * [ ] Memory usage < [X]MB
* **Deployment**:
    * [ ] Works in existing Docker container
    * [ ] No new build steps required
* **Anti-Patterns to Avoid**:
    * [ ] Manual user intervention
    * [ ] modifying `data/` directly without validation

## 4. User Experience / Interface
* **Inputs**: [Function arguments, API endpoints, or CLI flags]
* **Outputs**: [Return values, Files created, or Logs]
* **Example Usage**:
```python
# How user or system calls this
result = new_feature.run(param="value")
```

## 5. Implementation Plan
### Phase 1: Verification (Test First)
* [ ] Create `tests/test_[feature].py` with failing tests
* [ ] Define mocks for external APIs (Alpaca, LLM)

### Phase 2: Core Logic
* [ ] Implement `src/[module]/[feature].py`
* [ ] Add Pydantic models for validation

### Phase 3: Integration
* [ ] Wire into `TradingOrchestrator` or `Agent`
* [ ] Update `AGENTS.md` registry

## 6. Verification Steps
1. **Automated**: `pytest tests/test_[feature].py`
2. **Manual**: [e.g. "Run script X and check output Y"]
3. **Safety**: [e.g. "Verify no trades executed in dry-run"]
