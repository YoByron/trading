# Model Trainer Skill

**skill_id**: `model_trainer`
**Status**: ✅ Implemented
**Purpose**: Autonomous training of deep learning models (LSTM feature extractors)

## Overview

This skill automates the training of LSTM feature extractors for the trading system. It handles:
- Data collection verification
- Model training with configurable parameters
- Model validation and performance metrics
- Automatic retraining when needed
- Integration with RL framework

## Tools

### `train_lstm_model`
Train LSTM feature extractor on historical data.

**Parameters**:
- `symbols`: List of symbols to train on (default: ["SPY", "QQQ", "VOO"])
- `epochs`: Number of training epochs (default: 50)
- `batch_size`: Batch size (default: 32)
- `learning_rate`: Learning rate (default: 0.001)
- `seq_length`: Sequence length in timesteps (default: 60)
- `output_path`: Where to save model (default: "data/models/lstm_feature_extractor.pt")
- `device`: Device to train on ("cpu" or "cuda")

**Returns**:
- `model_path`: Path to saved model
- `training_metrics`: Loss, epochs, samples trained
- `validation_metrics`: Performance on validation set

### `check_training_data_availability`
Verify if sufficient historical data exists for training.

**Parameters**:
- `symbols`: List of symbols to check
- `min_days`: Minimum days required (default: 252)

**Returns**:
- `available`: Boolean indicating if data is sufficient
- `missing_symbols`: List of symbols with insufficient data
- `data_summary`: Summary of available data per symbol

### `schedule_retraining`
Schedule automatic model retraining based on performance degradation.

**Parameters**:
- `check_interval_days`: How often to check if retraining needed (default: 7)
- `performance_threshold`: Minimum performance to avoid retraining (default: 0.9)
- `auto_retrain`: Whether to automatically retrain if needed (default: True)

**Returns**:
- `scheduled`: Boolean indicating if retraining scheduled
- `next_check`: When next check will occur

## Integration

This skill integrates with:
- `src/agents/lstm_feature_extractor.py` - LSTM implementation
- `scripts/train_lstm_features.py` - Training script
- `src/utils/data_collector.py` - Data collection
- `src/orchestration/workflow_orchestrator.py` - Workflow automation

## Usage

```python
from claude_skills import load_skill

trainer_skill = load_skill("model_trainer")

# Check if data is available
data_check = trainer_skill.check_training_data_availability(
    symbols=["SPY", "QQQ", "VOO"],
    min_days=252
)

if data_check["available"]:
    # Train model
    result = trainer_skill.train_lstm_model(
        symbols=["SPY", "QQQ", "VOO"],
        epochs=50,
        batch_size=32
    )
    print(f"Model saved to: {result['model_path']}")
```

## Autonomous Operation

This skill can be triggered automatically by:
- Workflow orchestrator (weekly retraining)
- Performance monitor (when model performance degrades)
- Data agent (when new historical data is collected)
