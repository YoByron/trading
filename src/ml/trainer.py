import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import logging
import json
from datetime import datetime
from typing import Dict, Any

from src.ml.networks import LSTMPPO
from src.ml.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    Handles training and retraining of the LSTM-PPO model.
    Implements the 'Dynamic Retraining' pipeline.
    """
    
    def __init__(self, models_dir: str = "models/ml", device: str = "cpu"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.device = torch.device(device)
        self.data_processor = DataProcessor()
        
        # Hyperparameters
        self.input_dim = len(self.data_processor.feature_columns)
        self.hidden_dim = 128
        self.num_layers = 2
        self.learning_rate = 0.001
        self.batch_size = 32
        self.epochs = 50
        
    def train_supervised(self, symbol: str) -> Dict[str, Any]:
        """
        Pre-train the model using supervised learning (predicting price direction).
        This stabilizes the LSTM features before RL fine-tuning.
        """
        logger.info(f"Starting supervised training for {symbol}")
        
        # 1. Prepare Data
        df = self.data_processor.fetch_data(symbol, period="5y")
        if df.empty:
            return {"success": False, "error": "No data"}
            
        df = self.data_processor.add_technical_indicators(df)
        df = self.data_processor.normalize_data(df)
        
        # Create targets: 1 if next Close > current Close, else 0
        # We shift returns back by 1 to align 'current features' with 'next return'
        targets = (df['Returns'].shift(-1) > 0).astype(int).values
        
        # Create sequences
        X_tensor = self.data_processor.create_sequences(df)
        
        # Align targets with sequences (drop last row as it has no target, and align with sequence end)
        # X has length N - seq_len
        # targets should correspond to the day AFTER the sequence ends
        valid_len = len(X_tensor)
        # We need targets starting from index (seq_len - 1) up to end-1
        # Actually, create_sequences returns X[i : i+seq_len]. The target for this sequence is target[i + seq_len - 1] (next day return)
        # Let's simplify: just take the last valid_len targets
        y_tensor = torch.LongTensor(targets[self.data_processor.sequence_length : self.data_processor.sequence_length + valid_len])
        
        if len(X_tensor) == 0 or len(y_tensor) == 0:
             return {"success": False, "error": "Insufficient data for sequences"}

        # Split Train/Val
        train_size = int(0.8 * len(X_tensor))
        X_train, X_val = X_tensor[:train_size], X_tensor[train_size:]
        y_train, y_val = y_tensor[:train_size], y_tensor[train_size:]
        
        # 2. Initialize Model
        model = LSTMPPO(input_dim=self.input_dim, hidden_dim=self.hidden_dim, num_layers=self.num_layers).to(self.device)
        optimizer = optim.Adam(model.parameters(), lr=self.learning_rate)
        criterion = nn.CrossEntropyLoss() # For classification (Up/Down)
        
        # 3. Training Loop
        best_val_loss = float('inf')
        
        for epoch in range(self.epochs):
            model.train()
            optimizer.zero_grad()
            
            # Forward pass (using only Actor head for classification pre-training)
            # We ignore the Critic head for now
            action_probs, _, _ = model(X_train.to(self.device))
            
            # We map 3 actions (0:Hold, 1:Buy, 2:Sell) to 2 targets (0:Down, 1:Up)
            # For pre-training, let's just use a separate linear layer or project action_probs
            # Simplified: We treat Action 1 (Buy) as Up, Action 2 (Sell) as Down. Action 0 (Hold) is ignored or mapped.
            # Better approach for pre-training: Add a temporary classification head or just train the LSTM + Actor
            # Let's assume: Index 1 is Buy (Up), Index 2 is Sell (Down). We ignore Hold (0) for binary targets?
            # Or simpler: Just train it to output 2 classes. 
            # To keep architecture consistent, let's just use the first 2 outputs of Actor for Up/Down?
            # No, let's stick to the architecture. We want the Actor to learn "Buy" when price goes up.
            # So Target 1 (Up) -> Action 1 (Buy). Target 0 (Down) -> Action 2 (Sell).
            
            # Map binary targets to Action indices: 0->2 (Sell), 1->1 (Buy)
            y_train_mapped = torch.where(y_train == 1, torch.tensor(1), torch.tensor(2)).to(self.device)
            y_val_mapped = torch.where(y_val == 1, torch.tensor(1), torch.tensor(2)).to(self.device)
            
            loss = criterion(action_probs, y_train_mapped)
            loss.backward()
            optimizer.step()
            
            # Validation
            model.eval()
            with torch.no_grad():
                val_probs, _, _ = model(X_val.to(self.device))
                val_loss = criterion(val_probs, y_val_mapped)
                
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_model(model, symbol)
                
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Train Loss {loss.item():.4f}, Val Loss {val_loss.item():.4f}")
                
        return {
            "success": True,
            "symbol": symbol,
            "final_val_loss": best_val_loss.item(),
            "timestamp": datetime.now().isoformat()
        }

    def save_model(self, model: nn.Module, symbol: str):
        """Save model weights."""
        path = self.models_dir / f"{symbol}_lstm_ppo.pt"
        torch.save(model.state_dict(), path)
        logger.info(f"Saved best model for {symbol} to {path}")
        
    def load_model(self, symbol: str) -> LSTMPPO:
        """Load model weights."""
        path = self.models_dir / f"{symbol}_lstm_ppo.pt"
        model = LSTMPPO(input_dim=self.input_dim, hidden_dim=self.hidden_dim, num_layers=self.num_layers)
        if path.exists():
            model.load_state_dict(torch.load(path, map_location=self.device))
            model.to(self.device)
            logger.info(f"Loaded model for {symbol}")
        else:
            logger.warning(f"No existing model found for {symbol}, returning initialized model")
        return model

    def retrain_all(self, symbols: list) -> Dict[str, Any]:
        """
        Retrain models for all symbols.
        This is the entry point for the 'Dynamic Retraining' pipeline.
        """
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.train_supervised(symbol)
            except Exception as e:
                logger.error(f"Failed to retrain {symbol}: {e}")
                results[symbol] = {"success": False, "error": str(e)}
        return results
