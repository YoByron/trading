# Workflow Automation with AgentKit-Style Agents

**Date**: November 19, 2025  
**Status**: ✅ Implemented  
**Pattern**: Based on OpenAI's AgentKit and Model Context Protocol (MCP)

---

## Overview

This implementation brings AgentKit-style workflow automation to the trading system, enabling multi-step automated workflows with human-in-the-loop approval gates.

## Key Features

### 1. Workflow Automation Agents

**WorkflowAgent** (`src/agents/workflow_agent.py`):
- Email monitoring and processing workflows
- Automated report generation
- File processing (CSV imports/exports)
- Multi-step workflow execution

**ApprovalAgent** (`src/agents/approval_agent.py`):
- Human-in-the-loop approval workflows
- High-value trade approvals
- Risk limit override approvals
- Circuit breaker decisions
- Timeout handling

**NotificationAgent** (`src/agents/notification_agent.py`):
- Multi-channel notifications (Slack, Email, Dashboard, Log)
- Trade execution alerts
- Risk management alerts
- Approval request notifications

### 2. MCP Integrations

**Gmail MCP** (`mcp/servers/gmail.py`):
- Email monitoring
- Send emails
- Process attachments
- Email-based workflow triggers

**Slack MCP** (`mcp/servers/slack.py`):
- Optional - removed from defaults
- Send messages to channels (if configured)
- Send direct messages
- Formatted messages with block kit
- Trade alert formatting
- **Note**: Slack is optional - system uses email by default

**Google Sheets MCP** (`mcp/servers/google_sheets.py`):
- Read/write spreadsheet data
- Create formatted reports
- Update cells and ranges

### 3. Workflow Orchestrator

**WorkflowOrchestrator** (`src/orchestration/workflow_orchestrator.py`):
- Coordinates multi-step workflows
- Handles approval gates
- Error handling and retries
- State persistence
- Parallel and sequential step execution

## Usage Examples

### Email Monitoring Workflow

```python
from src.orchestration.workflow_orchestrator import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()

workflow = {
    "name": "Client Report Processing",
    "steps": [
        {
            "name": "monitor_email",
            "type": "mcp_call",
            "data": {
                "server": "gmail",
                "tool": "monitor_emails",
                "payload": {"query": "is:unread from:client@example.com"}
            }
        },
        {
            "name": "process_attachment",
            "type": "mcp_call",
            "data": {
                "server": "gmail",
                "tool": "process_attachment",
                "payload": {"message_id": "{previous_step.message_id}"}
            },
            "requires_approval": True
        }
    ]
}

result = await orchestrator.execute_workflow(workflow)
```

### High-Value Trade with Approval

```python
workflow = {
    "name": "High-Value Trade",
    "steps": [
        {
            "name": "analyze_market",
            "type": "mcp_call",
            "data": {
                "server": "openrouter",
                "tool": "detailed_sentiment",
                "payload": {"market_data": {"symbol": "SPY"}}
            }
        },
        {
            "name": "request_approval",
            "type": "approval",
            "data": {
                "approval_type": "trade",
                "context": {"symbol": "SPY", "trade_value": 5000.0},
                "priority": "high"
            },
            "requires_approval": True
        },
        {
            "name": "execute_trade",
            "type": "mcp_call",
            "data": {
                "server": "alpaca-trading",
                "tool": "submit_order",
                "payload": {"symbol": "SPY", "qty": 10, "side": "buy"}
            }
        }
    ]
}
```

## Configuration

### Environment Variables

```bash
# Approval thresholds
APPROVAL_HIGH_VALUE_THRESHOLD=1000.0  # Trades above this require approval

# Notification channels (Slack removed from defaults)
NOTIFICATION_CHANNELS=email,dashboard,log

# Approval notification channels
APPROVAL_NOTIFICATION_CHANNELS=email

# Google API Keys
GOOGLE_API_KEY=AIzaSy...  # Google Cloud API key
GEMINI_API_KEY=AIzaSy...  # Gemini API key
GOOGLE_PROJECT_ID=your-project-id

# Gmail (uses Google API key)
# No separate credentials needed if using Google API key

# Google Sheets (uses Google API key)
# No separate credentials needed if using Google API key

# Slack (optional - only if you want Slack notifications)
SLACK_BOT_TOKEN=xoxb-your-token  # Only needed if using Slack
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Workflow Orchestrator                      │
│  - Coordinates multi-step workflows                     │
│  - Manages approval gates                               │
│  - Handles error recovery                               │
└──────────────┬──────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                 │
┌──────▼──────┐   ┌──────▼──────────┐
│ Workflow    │   │ Approval        │
│ Agent       │   │ Agent           │
└──────┬──────┘   └──────┬──────────┘
       │                 │
       └────────┬────────┘
                │
       ┌────────▼──────────┐
       │ Notification      │
       │ Agent             │
       └────────┬──────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼───┐  ┌───▼──────┐
│ Gmail │  │ Slack │  │ Sheets   │
│ MCP   │  │ MCP   │  │ MCP      │
└───────┘  └───────┘  └──────────┘
```

## Integration with Existing System

The workflow automation integrates seamlessly with existing agents:

- **MCP Trading Orchestrator**: Can trigger workflows from trading decisions
- **Risk Agent**: Can request approvals for high-value trades
- **Execution Agent**: Can send notifications after trade execution
- **Meta Agent**: Can coordinate workflows as part of decision-making

## Next Steps

1. **Implement API Credentials**: Add actual Gmail, Slack, and Google Sheets API integrations
2. **Add More Workflows**: Create pre-built workflows for common tasks
3. **Dashboard Integration**: Add workflow monitoring to dashboard
4. **Workflow Templates**: Create reusable workflow templates
5. **Error Recovery**: Enhance retry logic and error handling

## References

- [OpenAI AgentKit Article](https://searchengineland.com/from-scripts-to-agents-openais-new-tools-unlock-the-next-phase-of-automation-464841)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [OpenAI AgentKit Documentation](https://platform.openai.com/docs/guides/agents)

