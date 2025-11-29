# MCP Code-Execution Harness

Anthropic recommends presenting MCP tools as importable code instead of dumping raw tool definitions into the model context to reduce token usage and improve reliability [source](https://www.anthropic.com/engineering/code-execution-with-mcp?utm_source=openai). This guide explains how to use the new harness and wrappers added under `mcp/`.

## 1. Environment Requirements
- Install the `claude` CLI (or another MCP-compatible client) and authenticate it with the broker/tool accounts you plan to use.
- Export `MCP_CLI_BIN` if the binary is not on `PATH`.
- Optionally export `MCP_PROFILE` when working with non-default CLI profiles.

```shell
export MCP_CLI_BIN="$HOME/.local/bin/claude"
export MCP_PROFILE="trading"
```

## 2. Registry Overview
- `mcp/registry.json` lists every server, the Python module that wraps it, and the tools each module exposes.
- `mcp/registry.py` loads the registry so other components can introspect available servers at runtime.
- Update this file whenever you add or remove a server. CI should diff the registry to detect schema drift.

## 3. Calling MCP Tools from Python
Use the typed wrappers in `mcp/servers/` to keep trading workflows inside the code-execution runtime:

```python
from mcp.servers import trade_agent, options_order_flow

trade_agent.place_equity_order(symbol="SPY", side="buy", quantity=10)
flow = options_order_flow.unusual_activity(symbol="NVDA")
```

All wrappers accept an optional `client=MCPClient(...)` argument if you want to override CLI defaults.

## 4. Running Tools via Harness CLI
Invoke any tool directly without loading definitions into context:

```shell
python -m mcp.harness trade-agent place_equity_order \
  --payload '{"symbol":"SPY","side":"buy","quantity":5}'
```

Use `--payload path/to/file.json` for larger request bodies, and `--output result.json` to persist responses.

## 5. Adding a New Server
1. Register the server in `mcp/registry.json`.
2. Create a wrapper under `mcp/servers/<name>.py` that calls `default_client().call_tool(...)`.
3. Add integration tests or scripts to cover expected workflows.
4. Document any secrets or environment variables required by the MCP server.

## 6. Security & Monitoring
- Run the harness inside a sandboxed environment because it executes subprocesses on demand.
- Use environment-specific CLI profiles so production credentials stay isolated from development runs.
- Capture CLI stdout/stderr with your logging pipeline to audit MCP activity.

Following this pattern keeps MCP usage code-driven and context-efficient, letting agents load only the tools they need while preserving full control over credentials and execution flow [source](https://www.anthropic.com/engineering/code-execution-with-mcp?utm_source=openai).
