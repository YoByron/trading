#!/bin/bash
# Enable ML Pipeline for Trading System
# Run this script to install ML dependencies and enable RL training
#
# Usage: ./scripts/enable_ml_pipeline.sh
#
# This installs:
# - PyTorch (neural network framework)
# - stable-baselines3 (RL algorithms)
# - gymnasium (RL environments)

set -e

echo "==============================================="
echo "ENABLING ML PIPELINE FOR TRADING SYSTEM"
echo "==============================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Run this from the trading project root directory"
    exit 1
fi

# Install ML dependencies
echo ""
echo "Installing ML dependencies (this may take a few minutes)..."
pip install torch>=2.0.0 gymnasium==0.29.1 stable-baselines3==2.3.2 --quiet

# Verify installation
echo ""
echo "Verifying installations..."
python3 -c "import torch; print('✅ PyTorch:', torch.__version__)"
python3 -c "import gymnasium; print('✅ Gymnasium:', gymnasium.__version__)"
python3 -c "import stable_baselines3; print('✅ stable-baselines3:', stable_baselines3.__version__)"

# Check audit trail for training data
AUDIT_FILE="data/audit_trail/hybrid_funnel_runs.jsonl"
if [ -f "$AUDIT_FILE" ] && [ -s "$AUDIT_FILE" ]; then
    LINES=$(wc -l < "$AUDIT_FILE")
    echo "✅ Audit trail: $LINES records available for training"
else
    echo "⚠️  Audit trail empty - need trading data before RL training"
    echo "   Run live trading first to collect training data"
fi

echo ""
echo "==============================================="
echo "ML PIPELINE STATUS"
echo "==============================================="
echo "Dependencies: INSTALLED"
echo "Training data: $([ -s "$AUDIT_FILE" ] && echo 'AVAILABLE' || echo 'PENDING')"
echo ""
echo "To train RL model, run:"
echo "  python scripts/rl_daily_retrain.py"
echo ""
echo "To enable RL in trading, set environment variable:"
echo "  export ENABLE_RL_TRAINING=true"
echo "==============================================="
