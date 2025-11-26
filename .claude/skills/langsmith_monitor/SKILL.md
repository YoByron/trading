# LangSmith Monitor Skill

**Purpose**: Continuous monitoring of LangSmith traces, runs, and performance metrics

## Overview

This skill provides comprehensive monitoring of LangSmith observability platform, tracking:
- LLM call traces and performance
- RL training runs and metrics
- System health and connectivity
- Token usage and costs
- Error rates and success metrics

## Usage

### Check Health

```python
from .claude.skills.langsmith_monitor.scripts.langsmith_monitor import LangSmithMonitor

monitor = LangSmithMonitor()
health = monitor.monitor_health()
```

### Get Recent Runs

```python
runs = monitor.get_recent_runs(
    project_name="trading-rl-training",
    hours=24,
    limit=50
)
```

### Get Project Statistics

```python
stats = monitor.get_project_stats(
    project_name="trading-rl-training",
    days=7
)
```

### Get Trace Details

```python
trace = monitor.get_trace_details(run_id="...")
```

## Integration

This skill is integrated into:
- Continuous monitoring system (`scripts/monitor_training_and_update_dashboard.py`)
- Progress Dashboard updates
- Training status tracking

## Requirements

- `LANGCHAIN_API_KEY` environment variable
- `langsmith` package installed

