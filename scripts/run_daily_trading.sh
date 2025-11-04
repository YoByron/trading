#!/bin/bash
# Daily Trading Execution Wrapper
# Ensures proper directory context for cron execution

cd /Users/igorganapolsky/workspace/git/apps/trading
/Users/igorganapolsky/workspace/git/apps/trading/venv/bin/python3 src/main.py --mode paper --run-once --strategy core
