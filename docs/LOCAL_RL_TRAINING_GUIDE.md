# Local RL Training Guide

## Why Train RL Locally?

**Current Setup:**
- ✅ Q-learning updates happen incrementally during trades (online learning)
- ❌ Deep RL (DQN/PPO) training is DISABLED (model-training.yml.disabled)
- ❌ No frequent batch training happening

**Why Local Training is Better:**
1. **Faster**: No CI/CD overhead, direct execution
2. **Cheaper**: No GitHub Actions compute costs
3. **More Frequent**: Can run hourly/daily vs weekly
4. **GPU Support**: Can use your GPU if available
5. **Better RL Performance**: More frequent training = better learning

---

## Recommended Training Frequency

### For Q-Learning (Online RL)
- **Current**: Updates every trade ✅ (already optimal)
- **Additional**: Run batch replay training every 1-2 hours during market hours
- **Command**: `python scripts/local_rl_training.py --agents q_learning --continuous --interval 3600`

### For Deep RL (DQN/PPO)
- **Current**: DISABLED ❌
- **Recommended**:
  - **During R&D Phase**: Daily after market close
  - **During Production**: Every 4-6 hours
- **Command**: `python scripts/local_rl_training.py --agents dqn,ppo --device cuda`

---

## Quick Start

### 1. Single Training Run
```bash
# Train Q-learning agent (fastest, always works)
python scripts/local_rl_training.py

# Train all RL agents
python scripts/local_rl_training.py --agents all

# Use GPU if available
python scripts/local_rl_training.py --device cuda
```

### 2. Continuous Training (Recommended)
```bash
# Train every 2 hours (good for market hours)
python scripts/local_rl_training.py --continuous --interval 7200

# Train every hour (more aggressive)
python scripts/local_rl_training.py --continuous --interval 3600

# Train daily after market close (4 PM ET = 8 PM UTC)
python scripts/local_rl_training.py --continuous --interval 86400
```

### 3. Background Process (macOS/Linux)
```bash
# Run in background, log to file
nohup python scripts/local_rl_training.py --continuous --interval 7200 > rl_training.log 2>&1 &

# Check if running
ps aux | grep local_rl_training

# Stop
pkill -f local_rl_training
```

---

## What Gets Trained

### Q-Learning Agent (Always Available)
- **What**: Online Q-learning with experience replay
- **When**: Every trade (automatic) + batch replay (via script)
- **Data**: Uses replay buffer from actual trades
- **Time**: <1 second per training run
- **Status**: ✅ Ready to use

### DQN Agent (Deep RL)
- **What**: Deep Q-Network with prioritized replay
- **When**: Needs batch training (32+ samples)
- **Data**: Requires trade history
- **Time**: 10-30 seconds per training run
- **Status**: ⚠️ Needs initialization (configure input/output dims)

### PPO Agent (Deep RL)
- **What**: Proximal Policy Optimization with LSTM
- **When**: Needs batch training (64+ samples)
- **Data**: Requires trade history + environment setup
- **Time**: 30-60 seconds per training run
- **Status**: ⚠️ Requires full environment setup

---

## Training Schedule Recommendations

### Option A: Aggressive (During R&D Phase)
```bash
# Run every hour during market hours (9 AM - 4 PM ET)
# Use cron or launchd

# macOS (launchd)
# Create ~/Library/LaunchAgents/com.trading.rl-training.plist
# Run: launchctl load ~/Library/LaunchAgents/com.trading.rl-training.plist
```

### Option B: Balanced (Recommended)
```bash
# Run every 2 hours during market hours
python scripts/local_rl_training.py --continuous --interval 7200
```

### Option C: Conservative (Production)
```bash
# Run daily after market close
python scripts/local_rl_training.py --continuous --interval 86400
```

---

## Monitoring Training

### Check Training Logs
```bash
# View latest training results
cat data/rl_training_log.json | jq '.[-1]'

# View all successful trainings
cat data/rl_training_log.json | jq '[.[] | select(.summary.success_rate > 0)]'

# Count training runs
cat data/rl_training_log.json | jq 'length'
```

### Check RL Agent State
```bash
# View Q-learning state
cat data/rl_policy_state.json | jq 'keys | length'  # Number of states learned

# View replay buffer size
python -c "from src.agents.reinforcement_learning_optimized import OptimizedRLPolicyLearner; a = OptimizedRLPolicyLearner(); print(f'Replay buffer: {len(a.replay_buffer)} samples')"
```

---

## Integration with GitHub Actions

**Keep GitHub Actions for:**
- ✅ Weekly validation/retraining (model-training.yml)
- ✅ Model versioning and deployment
- ✅ Cross-validation and backtesting

**Use Local Training for:**
- ✅ Frequent incremental learning
- ✅ Real-time adaptation
- ✅ Experimentation and iteration

---

## Troubleshooting

### "No RL state file found"
- **Cause**: Agent hasn't made any trades yet
- **Fix**: Run trading first, then training will work

### "Insufficient trade data"
- **Cause**: Need more trades for batch training
- **Fix**: Wait for more trades, or reduce batch_size in agent config

### "DQN agent not initialized"
- **Cause**: Need to configure input/output dimensions
- **Fix**: Initialize DQN agent with proper state/action space

### Training takes too long
- **Fix**: Use `--device cpu` instead of `cuda`, or reduce episodes

---

## Best Practices

1. **Start with Q-Learning**: Always works, no setup needed
2. **Train During Market Hours**: More relevant data
3. **Monitor Training Logs**: Check `data/rl_training_log.json`
4. **Don't Over-Train**: More frequent ≠ always better (can overfit)
5. **Use GPU for Deep RL**: Much faster for DQN/PPO

---

## Expected Results

After running local training:
- ✅ Q-learning agent improves decision-making
- ✅ Better trade selection over time
- ✅ Improved win rate and Sharpe ratio
- ✅ Faster adaptation to market changes

**Metrics to Watch:**
- Win rate trend (should improve)
- Sharpe ratio (should increase)
- Average reward per trade (should increase)
- Strategy health score (from dashboard)

---

## Next Steps

1. **Start Training**: `python scripts/local_rl_training.py --continuous --interval 7200`
2. **Monitor Results**: Check dashboard and training logs
3. **Adjust Frequency**: Based on your system performance
4. **Enable Deep RL**: Once you have enough trade data
