# Setup All Systems Workflow

---
**description**: Set up and ensure continuous operation of Grok AI, Gemini 3, Go ADK, LangChain, Claude agents, and RL agents on macOS.
---

## Prerequisites
1. **Python 3.14+** installed (already used by the project).
2. **Go 1.22+** installed (required for `trading_orchestrator`).
3. **Node.js 20+** (for any A2A server scripts).
4. Environment variables for API keys set in `~/.zshrc` or a `.env` file:
   ```bash
   export GROK_API_KEY="xai-..."
   export GEMINI_API_KEY="..."
   export CLAUDE_API_KEY="..."
   export ADK_ENABLED=1
   export LANGCHAIN_API_KEY="..."
   export RL_AGENT_KEY="..."
   ```
   Reload with `source ~/.zshrc`.

## 1. Create a launchd plist for the Go ADK orchestrator
Create the file `~/Library/LaunchAgents/com.trading.orchestrator.plist` with the following content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.trading.orchestrator</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/local/bin/go</string>
      <string>run</string>
      <string>./cmd/trading_orchestrator</string>
      <string>--data_dir</string>
      <string>/Users/igorganapolsky/workspace/git/apps/trading/data</string>
      <string>--log_path</string>
      <string>/Users/igorganapolsky/workspace/git/apps/trading/logs/adk_orchestrator.jsonl</string>
      <string>--app</string>
      <string>trading_orchestrator</string>
      <string>web</string>
      <string>--port</string>
      <string>8080</string>
      <string>api</string>
      <string>--webui_address</string>
      <string>localhost:8080</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/igorganapolsky/workspace/git/apps/trading</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>/Users/igorganapolsky/workspace/git/apps/trading/logs/orchestrator_stdout.log</string>
    <key>StandardErrorPath</key><string>/Users/igorganapolsky/workspace/git/apps/trading/logs/orchestrator_stderr.log</string>
  </dict>
</plist>
```
Load it with:
```bash
launchctl load ~/Library/LaunchAgents/com.trading.orchestrator.plist
```
It will now start on login and be automatically restarted if it crashes.

## 2. Create a launchd plist for the optional A2A server (Node.js)
If you have an `a2a-server.mjs` you want to keep alive, create `~/Library/LaunchAgents/com.trading.a2a.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.trading.a2a</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/local/bin/node</string>
      <string>/Users/igorganapolsky/workspace/git/apps/trading/path/to/a2a-server.mjs</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/igorganapolsky/workspace/git/apps/trading</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>/Users/igorganapolsky/workspace/git/apps/trading/logs/a2a_stdout.log</string>
    <key>StandardErrorPath</key><string>/Users/igorganapolsky/workspace/git/apps/trading/logs/a2a_stderr.log</string>
  </dict>
</plist>
```
Load with `launchctl load ~/Library/LaunchAgents/com.trading.a2a.plist`.

## 3. Python service starter script
Create `scripts/start_all_python.sh` to launch any long‑running Python agents (e.g., a background RL trainer, a LangChain server, Claude agent worker).
```bash
#!/usr/bin/env bash
set -euo pipefail

# Activate virtualenv
source /Users/igorganapolsky/workspace/git/apps/trading/venv/bin/activate

# Start LangChain server (if you have one)
nohup python -m src.agents.langchain_server > logs/langchain_stdout.log 2> logs/langchain_stderr.log &

# Start Claude agent worker (example placeholder)
nohup python -m src.agents.claude_worker > logs/claude_stdout.log 2> logs/claude_stderr.log &

# Start RL trainer daemon (example)
nohup python -m src.ml.rl_trainer > logs/rl_stdout.log 2> logs/rl_stderr.log &

echo "All Python services launched in background."
```
Make it executable:
```bash
chmod +x scripts/start_all_python.sh
```
Add this script to a launchd plist `~/Library/LaunchAgents/com.trading.python_services.plist` similar to the Go plist, pointing `ProgramArguments` to the script.

## 4. Verify everything is running
```bash
# Go orchestrator
curl http://localhost:8080/health

# LangChain (example endpoint)
curl http://localhost:8000/v1/models

# Claude worker – check its log file for "started"
tail -f logs/claude_stdout.log
```
If any service stops, `launchctl` will automatically restart it.

## 5. Updating / restarting
- To reload a plist after editing: `launchctl unload <path> && launchctl load <path>`.
- To stop a service temporarily: `launchctl unload <path>`.
- To view status: `launchctl list | grep com.trading`.

---
**End of workflow**
