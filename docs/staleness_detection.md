# Staleness Detection System

## Overview

The staleness detection system prevents hallucinations by refusing to load state data that is too old. This ensures the CTO never reports stale data as current.

## The Problem It Solves

**Incident: November 4, 2025**
- CTO read 5-day-old state (from Oct 30)
- Reported "Day 2" when it was actually "Day 7"
- Caused major CEO trust failure
- Root cause: No safeguards against stale data

## How It Works

### Staleness Thresholds

| Status | Age Range | Confidence | Behavior |
|--------|-----------|------------|----------|
| **FRESH** | <24 hours | 95% | Load silently |
| **AGING** | 24-48 hours | 70% | Warn but allow |
| **STALE** | 48-72 hours | 30% | Warn loudly but allow |
| **EXPIRED** | >72 hours (3 days) | 5% | **BLOCK LOAD** |

### Automatic Metadata

When loading state, the system automatically adds:

```json
{
  "meta": {
    "last_loaded": "2025-11-04T17:00:00",
    "staleness_hours": 126.9,
    "staleness_status": "EXPIRED",
    "self_evaluation": {
      "warnings": [
        "State is 5.3 days old - CRITICAL STALENESS",
        "Data is severely outdated and CANNOT be trusted",
        "Using this data WILL cause hallucinations"
      ],
      "recommendations": [
        "REQUIRED: Run daily_checkin.py immediately"
      ],
      "confidence_in_state": 0.05
    }
  }
}
```

### Console Warnings

For AGING, STALE, and EXPIRED states, loud warnings print to console:

```
======================================================================
⚠️  SYSTEM STATE WARNINGS ⚠️  [EXPIRED]
======================================================================
  ⚠️  State is 5.3 days old - CRITICAL STALENESS
  ⚠️  Data is severely outdated and CANNOT be trusted
  ⚠️  Using this data WILL cause hallucinations
  ⚠️  Challenge day calculation may be off by 5 days

RECOMMENDATIONS:
  → REQUIRED: Run daily_checkin.py immediately

Confidence in state: 5% (VERY LOW)
======================================================================
```

### EXPIRED State Blocking

If state is EXPIRED (>3 days), `StateManager` raises `ValueError` and refuses to load:

```
╔════════════════════════════════════════════════════════════════╗
║  CRITICAL ERROR: STATE DATA EXPIRED                            ║
╚════════════════════════════════════════════════════════════════╝

State last updated: 2025-10-30T10:00:00
Staleness: 126.9 hours (5.3 days)
Status: EXPIRED

⛔ REFUSING TO LOAD EXPIRED DATA ⛔

This prevents hallucinations where the system reports old data as current.

ACTION REQUIRED:
1. Run daily_checkin.py to refresh state with current data
2. Or manually update system_state.json with current account data
```

## Implementation Details

### Files Modified

- `/scripts/state_manager.py` - Core staleness detection logic

### Key Methods

#### `_add_staleness_metadata(state)`
Calculates staleness and adds metadata to state dict

#### `_evaluate_state_quality(state)`
Evaluates state quality, generates warnings, prints to console

#### `load_state()`
Enhanced to call staleness detection and block EXPIRED states

#### `save_state()`
Clears staleness metadata when saving fresh data

## Testing

### Test Suite

Run comprehensive tests:
```bash
python3 scripts/test_staleness.py
```

Tests all four staleness levels:
- FRESH (12 hours) - loads silently
- AGING (36 hours) - warns but allows
- STALE (60 hours) - warns loudly but allows
- EXPIRED (96 hours) - blocks with error

### Hallucination Prevention Demo

Demonstrate the exact Oct 30 hallucination being prevented:
```bash
python3 scripts/demonstrate_hallucination_prevention.py
```

## Usage

### Normal Operation

StateManager automatically runs staleness detection on every load:

```python
from state_manager import StateManager

# This will check staleness automatically
sm = StateManager()  # Prints warnings if AGING/STALE, raises error if EXPIRED
```

### Handling EXPIRED State

If you encounter EXPIRED state error:

```bash
# Option 1: Run daily checkin to refresh state
python3 scripts/daily_checkin.py

# Option 2: Manually update state file with current data
# (only if daily_checkin.py is not available)
```

## Benefits

1. **Prevents Hallucinations**: Impossible to report old data as current
2. **Loud Warnings**: Visual alerts when data is getting stale
3. **Forced Refresh**: EXPIRED states cannot be used
4. **Automatic**: No manual checks needed
5. **Self-Documenting**: Warnings explain the problem and solution

## CEO Mandate

> "I never want to see you hallucinate again."

This system fulfills that mandate by making stale data hallucinations **structurally impossible**.

## Future Enhancements

Potential improvements:
- Configurable thresholds per environment (dev vs prod)
- Email alerts for STALE states
- Auto-refresh mechanism when state becomes AGING
- Staleness tracking in dashboard
