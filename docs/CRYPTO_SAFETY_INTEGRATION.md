# Crypto Strategy - Graham-Buffett Safety Integration

## Status: ✅ **INTEGRATED**

The crypto trading strategy now includes Graham-Buffett safety checks before executing trades.

## Integration Details

### What Was Added

1. **Safety Analysis Before Crypto Trades**
   - Margin of Safety check (if DCF data available)
   - Quality company screening (fundamentals, debt, earnings)
   - Circle of competence enforcement
   - Safety rating assignment

2. **Location**: `src/strategies/crypto_strategy.py`
   - Integrated in `execute_daily()` method
   - Runs before trade execution (Step 3.5)
   - Can be disabled via `USE_GRAHAM_BUFFETT_SAFETY=false`

### Weekend Execution Schedule

**GitHub Actions Workflow**: `.github/workflows/weekend-crypto-trading.yml`

- **Schedule**: Saturdays and Sundays at 10:00 AM Eastern
- **Cron**: `0 15 * * 0,6` (15:00 UTC = 10:00 AM ET)
- **Note**: Cron needs updating when DST changes (March/November)

**Local Execution**: `scripts/autonomous_trader.py`
- Automatically detects weekends (Saturday=5, Sunday=6)
- Switches to crypto mode on weekends
- Can force with `--crypto-only` flag

## How It Works

### Weekend Detection

```python
def is_weekend():
    """Check if today is Saturday or Sunday."""
    return datetime.now().weekday() in [5, 6]  # Saturday=5, Sunday=6
```

### Crypto Strategy Execution Flow

1. **Weekend Detection**: System checks if it's Saturday or Sunday
2. **Crypto Strategy Initialization**: Creates `CryptoStrategy` instance
3. **Safety Check** (NEW): Graham-Buffett safety analysis
   - Checks margin of safety (if available)
   - Screens for quality
   - Enforces circle of competence
4. **Trade Execution**: Only proceeds if safety check passes

### Safety Check for Crypto

**Note**: Crypto assets (BTC, ETH) may not have traditional DCF/intrinsic value data, so:

- ✅ **Circle of Competence**: BTC and ETH are in well-known list
- ✅ **Quality Screening**: Will check if fundamentals available
- ⚠️ **Margin of Safety**: May not be available (DCF calculation may fail)
- ✅ **Fail-Open**: If DCF fails, trade can still proceed (crypto-specific behavior)

## Configuration

### Environment Variables

```bash
# Enable/disable Graham-Buffett safety (default: true)
USE_GRAHAM_BUFFETT_SAFETY=true

# Crypto daily investment amount
CRYPTO_DAILY_AMOUNT=0.50
```

### Disable Safety for Crypto

If you want to disable safety checks for crypto (not recommended):

```bash
USE_GRAHAM_BUFFETT_SAFETY=false
```

## Testing

### Manual Test

```bash
# Force crypto execution (any day)
python3 scripts/autonomous_trader.py --crypto-only

# Normal execution (auto-detects weekend)
python3 scripts/autonomous_trader.py
```

### Expected Behavior

1. **Safety Check Runs**: You'll see logs like:
   ```
   ✅ BTCUSD PASSED Graham-Buffett Safety Check (Rating: acceptable)
      Margin of Safety: N/A (DCF unavailable for crypto)
      Quality Score: N/A
   ```

2. **Trade Rejection**: If safety check fails:
   ```
   🚨 BTCUSD REJECTED by Graham-Buffett Safety Module
      Safety Rating: reject
      Reason: [reason]
   SKIPPING CRYPTO TRADE - Failed Graham-Buffett safety check
   ```

## Weekend Workflow Status

### Last Execution

Check GitHub Actions for last weekend execution:
- **Workflow**: `weekend-crypto-trading.yml`
- **Schedule**: Saturdays and Sundays at 10:00 AM ET
- **Logs**: Available in Actions → Artifacts

### Verification

To verify the weekend workflow ran:

1. **Check GitHub Actions**:
   - Go to: https://github.com/IgorGanapolsky/trading/actions
   - Look for "Weekend Crypto Trading" workflow
   - Check last run date

2. **Check Logs**:
   ```bash
   tail -100 logs/cron_trading.log | grep -i crypto
   ```

3. **Check System State**:
   ```bash
   cat data/system_state.json | grep -i crypto
   ```

## Troubleshooting

### Crypto System Not Running on Weekends

1. **Check GitHub Actions Schedule**:
   - Verify cron expression is correct
   - Check if workflow is enabled
   - Verify DST adjustments (March/November)

2. **Check Local Scheduler**:
   - Verify cron job exists (if using local scheduler)
   - Check cron logs: `grep CRON /var/log/syslog`

3. **Manual Test**:
   ```bash
   python3 scripts/autonomous_trader.py --crypto-only
   ```

### Safety Check Failing for Crypto

**Expected Behavior**: Crypto may not have DCF data, so margin of safety may be unavailable. The system will:
- Still check circle of competence (BTC/ETH are approved)
- Still check quality if available
- Fail-open if DCF unavailable (allows trade to proceed)

**If you want stricter checks**:
- Modify `crypto_strategy.py` to require safety approval
- Or disable fail-open behavior

## Future Enhancements

- [ ] Crypto-specific intrinsic value models (not DCF)
- [ ] On-chain metrics for quality screening
- [ ] Network health indicators
- [ ] DeFi protocol risk assessment

---

**Last Updated**: 2025-01-XX
**Integration Status**: ✅ Complete
**Next Weekend Execution**: Check GitHub Actions schedule
