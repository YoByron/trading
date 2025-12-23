---
layout: post
title: "Lesson Learned #058: 68% LangSmith Trace Error Rate - Silent Bugs Hiding in Observability Code"
date: 2025-12-23
---

# Lesson Learned #058: 68% LangSmith Trace Error Rate - Silent Bugs Hiding in Observability Code

## The Failure

LangSmith dashboard showed **68% error rate** across 304 runs - two-thirds of all trace attempts were silently failing. The observability system meant to help us debug was itself broken, and we had no idea.

## Root Causes (7 Bugs Found)

### Bug 1: Silent Exception Swallowing
**File**: `src/orchestrator/gates.py:78`
```python
# BAD - All tracing errors completely hidden
except Exception as e:
    logger.debug("Gate tracing failed: %s", e)  # Nobody reads debug logs
```

### Bug 2: Double Span Completion
**Files**: `orchestrator_hooks.py:57` + `langsmith_tracer.py:369`

Both the wrapper function AND the context manager tried to complete the span on error, corrupting trace state.

### Bug 3: AttributeError in Trace Inputs
**File**: `gates.py:1052`
```python
# BAD - ctx.macd_signal doesn't exist!
{"gate": 1, "has_macd": ctx.macd_signal is not None}

# GOOD - Use actual attribute
{"gate": 1, "has_momentum": ctx.momentum_signal is not None}
```

### Bug 4: Wrong Schema for Extra Field
**File**: `langsmith_tracer.py:405`
```python
# BAD - Nested structure
extra={"metadata": span.metadata}

# GOOD - Flat structure
extra=span.metadata
```

### Bug 5: Empty Name Validation
Spans could have empty names, causing LangSmith API validation failures.

### Bug 6: Inconsistent Project Names
Three different defaults across files: "trading-system", "igor-trading-system", "trading-rl-training"

### Bug 7: Deprecated Datetime
Using `datetime.utcnow()` instead of timezone-aware `datetime.now(timezone.utc)`

## Impact

- **68% of traces lost** - Most debugging information never recorded
- **Blind to failures** - Couldn't diagnose trading issues
- **False confidence** - Thought observability was working
- **Wasted LangSmith budget** - Paying for traces that failed

## The Fix

1. Changed silent `logger.debug` to `logger.warning` for visibility
2. Removed manual `span.complete()` - let context manager handle it
3. Fixed attribute name: `macd_signal` → `momentum_signal`
4. Flattened extra field schema
5. Added fallback name for empty spans
6. Unified project name to `igor-trading-system`
7. Updated to timezone-aware datetime
8. Added CI verification step before trading

## Prevention Rules

1. **Test your observability** - If you can't verify traces are working, assume they're not
2. **Never swallow exceptions silently** - At minimum use `logger.warning`
3. **Add CI verification** - `verify_langsmith.py` now runs before every trading session
4. **Check error rates** - 68% should have triggered an alert
5. **Validate against schema** - Test trace format before production

## Code Verification Pattern

```python
# verify_langsmith.py - Run before trading
def verify_langsmith() -> bool:
    client = Client()
    now = datetime.now(timezone.utc)
    client.create_run(
        name="ci_verification_trace",
        inputs={"test": "verification"},
        outputs={"status": "ok"},
        run_type="chain",
        project_name="igor-trading-system",
        start_time=now,
        end_time=now,
        tags=["verification", "ci"],
    )
    return True
```

## Key Insight

> "The observability system is the last place you expect bugs, but it's also the last place you'd notice them."

If your traces aren't working, you won't see the errors telling you your traces aren't working. This is a dangerous blind spot.

## Tags

`langsmith` `observability` `silent-failures` `debugging` `tracing` `ci-verification`
