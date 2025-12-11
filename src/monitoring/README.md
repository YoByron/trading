# Trading System Monitoring

Continuous monitoring daemon and health checks for the trading system.

## Overview

Created after the Dec 11, 2025 incident where a syntax error caused zero trades for an entire day. This monitoring system provides:

1. **Continuous Daemon** - Background process that monitors everything
2. **Health Monitor** - Quick checks for use in CI/cron
3. **GitHub Actions** - Scheduled health checks every 15 minutes

## Components

### Trading Daemon (`trading_daemon.py`)

Full-featured monitoring daemon that runs continuously.

```bash
# Run as daemon
python3 -m src.monitoring.trading_daemon

# Run once (for testing)
python3 -m src.monitoring.trading_daemon --once

# With notifications
python3 -m src.monitoring.trading_daemon \
    --github-token $GITHUB_TOKEN \
    --slack-webhook $SLACK_WEBHOOK
```

**Checks performed:**
- ✅ Trades executing during market hours
- ✅ GitHub Actions workflow status
- ✅ System health (syntax errors, imports)
- ✅ Performance metrics
- ✅ Records incidents to RAG

**Alerts via:**
- Console/logs
- Slack webhook
- GitHub Issues (auto-created)

### Health Monitor (`health_monitor.py`)

Lightweight health checks for quick status.

```bash
# Quick health check
python3 -m src.monitoring.health_monitor
```

Returns JSON with:
- Trade count today
- Syntax validation
- Market status
- Last trade timestamp

### GitHub Actions (`health-monitor.yml`)

Automated health checks every 15 minutes during market hours.

- Runs Mon-Fri, 9:30 AM - 4:00 PM ET
- Creates GitHub Issues for critical alerts
- Integrates with continuous verifier

## Deployment

### As systemd Service

```bash
# Copy service file
sudo cp deploy/trading-daemon.service /etc/systemd/system/

# Edit configuration
sudo nano /etc/systemd/system/trading-daemon.service
# Set GITHUB_TOKEN and SLACK_WEBHOOK

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable trading-daemon
sudo systemctl start trading-daemon

# Check status
sudo systemctl status trading-daemon
sudo journalctl -u trading-daemon -f
```

### As Docker Container

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python3", "-m", "src.monitoring.trading_daemon"]
```

### As Cron Job

```bash
# Health check every 15 minutes during market hours
*/15 9-16 * * 1-5 cd /opt/trading && python3 -m src.monitoring.health_monitor >> /var/log/trading/health.log 2>&1
```

## Alert Levels

| Level | Description | Action |
|-------|-------------|--------|
| `info` | Normal status | Log only |
| `warning` | Potential issue | Log + monitor |
| `critical` | Immediate action needed | Log + notify + GitHub Issue |

## Critical Alerts

These trigger immediate notifications:

1. **no_trades_today** - No trades file exists during market hours
2. **syntax_error** - Critical file has syntax error
3. **workflow_failure** - GitHub Actions workflow failed
4. **daemon_failure** - Daemon itself is failing

## Integration with RAG

All critical alerts are automatically recorded to the lessons learned RAG:

```python
from src.verification.rag_safety_checker import RAGSafetyChecker

checker = RAGSafetyChecker()
checker.record_incident(
    category="daemon_alert",
    title="...",
    description="...",
    ...
)
```

This ensures the system learns from issues and can prevent similar problems.

## Configuration

Environment variables:
- `GITHUB_TOKEN` - For GitHub API (workflow status, issue creation)
- `SLACK_WEBHOOK` - For Slack notifications

Config options (in code):
- `check_interval_seconds` - How often to run checks (default: 300)
- `min_daily_trades` - Minimum expected trades (default: 1)
- `max_consecutive_failures` - Before alerting daemon failure (default: 3)

## Related

- `src/verification/` - Pre-merge and continuous verification
- `rag_knowledge/lessons_learned/ll_009_*` - Dec 11 incident documentation
- `.github/workflows/verification-gate.yml` - CI verification gate
