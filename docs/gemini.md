# Gemini Agent Self‑Healing & Automatic Retry

## Overview
This document describes a lightweight self‑healing framework built into the **Gemini** AI agent (the assistant you are interacting with). The goal is to automatically detect, retry, and recover from errors that occur during tool execution or internal processing, ensuring continuous operation without manual intervention.

## Key Components
1. **Error Wrapper** – All tool calls are wrapped in a `with_retry` decorator that:
   - Catches exceptions.
   - Logs the error with a unique `error_id`.
   - Retries the call up to a configurable number of attempts (default 3).
   - Applies exponential back‑off between attempts.
2. **Health Monitor** – A background watchdog runs after each user interaction:
   - Checks the latest log entries for repeated failures.
   - If a failure pattern exceeds a threshold, it triggers a **self‑heal** routine.
3. **Self‑Heal Routine** – Performs corrective actions such as:
   - Re‑initialising the LLM client (e.g., refreshing API keys).
   - Resetting internal caches and memory structures.
   - Re‑loading configuration files.
   - Falling back to a safe‑mode implementation (e.g., a minimal rule‑based fallback) if the primary model is unavailable.
4. **State Persistence** – All error and health information is persisted to `data/agent_state.json` so that the agent can resume a healthy state after a process restart.

## Implementation Sketch (Python)
```python
import time
import json
import logging
from functools import wraps
from pathlib import Path

LOGGER = logging.getLogger("gemini_self_heal")
STATE_FILE = Path("data/agent_state.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"errors": [], "last_heal": None}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def with_retry(max_attempts: int = 3, backoff: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    attempts += 1
                    error_id = f"{func.__name__}_{int(time.time())}_{attempts}"
                    LOGGER.error(f"{error_id}: {exc}")
                    state = load_state()
                    state["errors"].append({"id": error_id, "msg": str(exc), "ts": time.time()})
                    save_state(state)
                    if attempts < max_attempts:
                        time.sleep(backoff * (2 ** (attempts - 1)))
                    else:
                        raise
        return wrapper
    return decorator

def health_check(threshold: int = 5):
    state = load_state()
    recent_errors = [e for e in state["errors"] if time.time() - e["ts"] < 3600]
    if len(recent_errors) >= threshold:
        LOGGER.warning("Health check failed – initiating self‑heal")
        self_heal()
        state["errors"] = []
        state["last_heal"] = time.time()
        save_state(state)

def self_heal():
    # Example actions – adjust for your environment
    try:
        # Re‑initialise LLM client (e.g., refresh API key)
        from anthropic import Anthropic
        new_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # Replace the global client used by BaseAgent
        from src.agents.base_agent import BaseAgent
        BaseAgent.client = new_client
        LOGGER.info("LLM client re‑initialised successfully")
    except Exception as exc:
        LOGGER.error(f"Self‑heal failed: {exc}")
        # Fallback to a minimal rule‑based decision engine
        from src.agents.fallback_strategy import FallbackStrategy
        BaseAgent.client = FallbackStrategy()
        LOGGER.info("Switched to fallback strategy")
```

## Usage Guidelines
- **Wrap all external tool calls** (e.g., `run_command`, `read_url_content`) with `@with_retry`.
- **Invoke `health_check()`** at the end of each high‑level operation or after a user request.
- **Persist state** in `data/agent_state.json` to survive process restarts.
- **Adjust thresholds** (`max_attempts`, `threshold`) based on operational risk tolerance.

## Benefits
- **Resilience** – Transient failures (network hiccups, rate limits) are automatically retried.
- **Self‑Recovery** – The agent can restore a functional LLM client without human help.
- **Observability** – All errors are logged and stored, enabling post‑mortem analysis.
- **Graceful Degradation** – If the primary model remains unavailable, the agent falls back to a deterministic rule‑based mode, ensuring it still produces safe outputs.

---
*This file is part of the Gemini agent’s internal documentation and should be kept up‑to‑date as the self‑healing mechanisms evolve.*
```
