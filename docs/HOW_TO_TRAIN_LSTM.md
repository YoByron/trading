# How to Train the LSTM Feature Extractor

This guide walks you through training the LSTM model for deep learning trading signals.

---

## Prerequisites

1. **Historical Data**: You need at least 252 days (1 year) of historical data
2. **Dependencies**: PyTorch and scikit-learn installed
3. **Python Environment**: Virtual environment activated

---

## Step-by-Step Training Process

### Step 1: Collect Historical Data

First, ensure you have historical data for the symbols you want to train on:

```bash
# Collect 1 year of data for core ETF universe
python scripts/populate_historical_data.py \
    --symbols SPY,QQQ,VOO,BND \
    --lookback 252
```

**What this does:**
- Fetches 252 days (~1 year) of OHLCV data
- Saves to `data/historical/` directory
- Creates CSV files: `SPY_YYYY-MM-DD.csv`, etc.

**Requirements:**
- API keys configured (ALPACA_API_KEY or POLYGON_API_KEY)
- See `docs/ENVIRONMENT_VARIABLES.md` for setup

---

### Step 2: Train the LSTM Model

Once you have historical data, train the model:

```bash
# Basic training (default settings)
python scripts/train_lstm_features.py \
    --symbols SPY,QQQ,VOO \
    --epochs 50

# Advanced training (custom settings)
python scripts/train_lstm_features.py \
    --symbols SPY,QQQ,VOO \
    --epochs 100 \
    --batch-size 64 \
    --learning-rate 0.0005 \
    --seq-length 60 \
    --output data/models/lstm_feature_extractor.pt \
    --device cpu
```

**Parameters:**
- `--symbols`: Comma-separated list of symbols to train on
- `--epochs`: Number of training epochs (default: 50)
- `--batch-size`: Batch size for training (default: 32)
- `--learning-rate`: Learning rate (default: 0.001)
- `--seq-length`: Sequence length in timesteps (default: 60)
- `--output`: Where to save the trained model
- `--device`: `cpu` or `cuda` (GPU) if available

**What happens during training:**
1. Loads historical data for each symbol
2. Creates sliding window sequences (60 timesteps each)
3. Calculates 35+ features per timestep (technical indicators)
4. Trains LSTM to predict future returns (5 days ahead)
5. Saves trained model to disk

**Expected Output:**
```
======================================================================
LSTM Feature Extractor Training
======================================================================
Symbols: SPY,QQQ,VOO
Epochs: 50
Device: cpu
======================================================================
Loading data for SPY...
Created 192 sequences
Sequence shape: (192, 60, 35) (samples, timesteps, features)
SPY: 192 sequences
Loading data for QQQ...
...
Total training samples: 576
Starting training...
Training LSTM: input_dim=35, seq_length=60
Epoch 10/50, Loss: 0.001234
Epoch 20/50, Loss: 0.000987
...
Training complete

✅ Model saved to: data/models/lstm_feature_extractor.pt
```

---

### Step 3: Verify Training Success

Check that the model was saved:

```bash
ls -lh data/models/lstm_feature_extractor.pt
```

You should see a `.pt` file (PyTorch model checkpoint).

---

## How It Works

### Architecture

```
Historical Data (OHLCV)
    ↓
Feature Extraction (35+ features per timestep)
    ↓
Sliding Window Sequences (60 timesteps × 35 features)
    ↓
LSTM Network (2 layers, 128 hidden units)
    ↓
Feature Vector (50 dimensions)
    ↓
RL State Space (for OptimizedRLPolicyLearner)
```

### Training Objective

The LSTM is trained to predict **future returns** (5 days ahead):
- **Input**: 60 timesteps of market features
- **Output**: Predicted return (price change %)
- **Loss**: Mean Squared Error (MSE)

This supervised pre-training helps the LSTM learn temporal patterns before being used for reinforcement learning.

---

## Troubleshooting

### "No training data available"

**Problem**: Script can't find historical data

**Solution**:
```bash
# Check if data exists
ls data/historical/

# If empty, collect data first
python scripts/populate_historical_data.py --symbols SPY,QQQ,VOO --lookback 252
```

### "Insufficient data for {symbol}"

**Problem**: Not enough historical bars

**Solution**:
- Collect more data: `--lookback 252` (1 year)
- Or reduce `--seq-length` (default: 60)

### "CUDA out of memory" (GPU training)

**Problem**: GPU runs out of memory

**Solution**:
- Reduce batch size: `--batch-size 16`
- Or use CPU: `--device cpu`

### Loss not decreasing

**Problem**: Model not learning

**Solutions**:
- Increase epochs: `--epochs 100`
- Lower learning rate: `--learning-rate 0.0001`
- Check data quality (ensure historical data is valid)

---

## Next Steps After Training

1. **Integrate with RL**: Modify `OptimizedRLPolicyLearner` to use LSTM features
2. **Test on Live Data**: Extract features from current market data
3. **A/B Test**: Compare LSTM-PPO vs. current strategy

---

## Example: Full Training Workflow

```bash
# 1. Collect data
python scripts/populate_historical_data.py \
    --symbols SPY,QQQ,VOO,BND \
    --lookback 252

# 2. Train model
python scripts/train_lstm_features.py \
    --symbols SPY,QQQ,VOO \
    --epochs 50 \
    --batch-size 32 \
    --output data/models/lstm_feature_extractor.pt

# 3. Verify
python -c "
from src.agents.lstm_feature_extractor import LSTMPPOWrapper
wrapper = LSTMPPOWrapper(model_path='data/models/lstm_feature_extractor.pt')
print('✅ Model loaded successfully')
"
```

---

## Performance Tips

1. **More Data = Better**: Use 252+ days (1 year) for robust training
2. **Multiple Symbols**: Train on SPY, QQQ, VOO together for diversity
3. **GPU Acceleration**: Use `--device cuda` if you have a GPU (much faster)
4. **Hyperparameter Tuning**: Experiment with learning rate, batch size, epochs

---

**Last Updated**: November 25, 2025

