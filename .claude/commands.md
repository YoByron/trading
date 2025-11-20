# Trading System Slash Commands

This file defines custom slash commands for the trading system. These commands provide quick access to common trading operations and analysis tasks.

## Available Commands

### `/backtest`
**Purpose**: Run a backtest of the trading strategy  
**Script**: `scripts/run_backtest_now.py`  
**Usage**: `/backtest [--days 60] [--symbol SPY]`  
**Description**: Executes a backtest of the momentum strategy (MACD + RSI + Volume) over the specified period. Defaults to 60 days if not specified.

**Example**:
```
/backtest --days 60 --symbol SPY
```

**Output**: Backtest results including win rate, Sharpe ratio, total return, and trade-by-trade analysis.

---

### `/verify-trades`
**Purpose**: Verify recent trades and execution accuracy  
**Script**: `scripts/verify_execution.py`  
**Usage**: `/verify-trades [--days 7]`  
**Description**: Verifies that trades executed correctly by comparing Alpaca API data with system state. Checks for order size errors, execution accuracy, and position tracking.

**Example**:
```
/verify-trades --days 7
```

**Output**: Verification report showing:
- Trade execution accuracy
- Order size validation
- Position tracking status
- Any discrepancies found

---

### `/analyze-performance`
**Purpose**: Generate comprehensive performance analysis  
**Script**: `scripts/daily_report.py`  
**Usage**: `/analyze-performance [--days 30]`  
**Description**: Analyzes trading performance over the specified period. Includes win rate, P/L analysis, position tracking, and system health metrics.

**Example**:
```
/analyze-performance --days 30
```

**Output**: Performance report including:
- Win rate and Sharpe ratio
- Total P/L and daily averages
- Position analysis (open/closed)
- System reliability metrics
- Recommendations

---

### `/health-check`
**Purpose**: Run pre-market health check  
**Script**: `scripts/pre_market_health_check.py`  
**Usage**: `/health-check`  
**Description**: Validates system readiness before trading. Checks API connectivity, market status, circuit breakers, and data sources.

**Example**:
```
/health-check
```

**Output**: Health check report showing:
- API connectivity status
- Market open/closed status
- Circuit breaker status
- Data source availability
- System readiness recommendation

---

### `/preflight`
**Purpose**: Run comprehensive pre-flight check  
**Script**: `scripts/preflight_check.py`  
**Usage**: `/preflight`  
**Description**: Performs comprehensive system readiness check including environment variables, code fixes, performance log freshness, and workflow configuration.

**Example**:
```
/preflight
```

**Output**: Pre-flight check report showing:
- Environment variables status
- Code fixes verification
- Performance log freshness
- System state freshness
- Workflow configuration
- Overall readiness status

---

## Implementation Notes

These commands are designed to be invoked from Claude's chat interface. When a user types a slash command, Claude should:

1. **Parse the command** and extract arguments
2. **Execute the corresponding script** with appropriate arguments
3. **Format the output** for readability
4. **Handle errors gracefully** with clear error messages

## Adding New Commands

To add a new slash command:

1. Create or identify the script that performs the operation
2. Add an entry to this file with:
   - Command name and purpose
   - Script path
   - Usage syntax
   - Description
   - Example
   - Expected output

3. Update `.claude/CLAUDE.md` to reference this commands file

## Command Execution Pattern

All commands follow this pattern:
```python
# Parse arguments
args = parse_args()

# Execute script
result = subprocess.run(
    ['python3', 'scripts/script_name.py'] + args,
    capture_output=True,
    text=True
)

# Format and return output
return format_output(result.stdout, result.stderr)
```


