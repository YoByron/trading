import pandas as pd
import numpy as np
import torch
from typing import List, Tuple, Dict, Optional
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Handles data fetching, feature engineering, and preprocessing for the ML model.
    """
    
    def __init__(self, sequence_length: int = 60, feature_columns: List[str] = None):
        self.sequence_length = sequence_length
        self.feature_columns = feature_columns or [
            'Close', 'Volume', 'Returns', 'RSI', 'MACD', 'Signal', 'Volatility',
            'Bogleheads_Sentiment', 'Bogleheads_Regime', 'Bogleheads_Risk'  # Bogleheads features
        ]
        self.scalers = {}  # Store scalers per symbol if needed
        
    def fetch_data(self, symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
        """Fetch historical data using yfinance."""
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return df
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the DataFrame."""
        if df.empty:
            return df
            
        df = df.copy()
        
        # Ensure we are working with single-level columns if MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 1. Returns
        df['Returns'] = df['Close'].pct_change()
        
        # 2. RSI (14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 3. MACD (12, 26, 9)
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # 4. Volatility (20-day rolling std dev)
        df['Volatility'] = df['Returns'].rolling(window=20).std()
        
        # 5. Volume Change
        df['Volume_Change'] = df['Volume'].pct_change()
        
        # Fill NaNs
        df.fillna(0, inplace=True)
        
        return df

    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize features using Z-score normalization (StandardScaler logic)."""
        df_norm = df.copy()
        
        for col in self.feature_columns:
            if col in df_norm.columns:
                mean = df_norm[col].mean()
                std = df_norm[col].std()
                if std != 0:
                    df_norm[col] = (df_norm[col] - mean) / std
                else:
                    df_norm[col] = 0.0
                    
        return df_norm

    def create_sequences(self, df: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Create sequences for LSTM input.
        
        Returns:
            X: Tensor of shape (num_samples, sequence_length, num_features)
            y: Tensor of shape (num_samples,) - Target (next day return direction: 0=Hold/Sell, 1=Buy)
               Note: This is a simplified target for pre-training/supervised check. 
               For PPO RL, we use the environment interaction, not static targets.
        """
        data = df[self.feature_columns].values
        
        X = []
        
        # We need at least sequence_length rows
        if len(data) <= self.sequence_length:
            return torch.tensor([]), torch.tensor([])
            
        for i in range(len(data) - self.sequence_length):
            X.append(data[i : i + self.sequence_length])
            
        return torch.FloatTensor(np.array(X))

    def prepare_inference_data(self, symbol: str) -> Optional[torch.Tensor]:
        """
        Prepare the latest sequence for inference.
        Includes Bogleheads features if available.
        """
        df = self.fetch_data(symbol, period="6mo") # Fetch enough for indicators + sequence
        if df.empty:
            return None
            
        df = self.add_technical_indicators(df)
        df = self.normalize_data(df)
        
        # Get the last sequence_length rows
        if len(df) < self.sequence_length:
            logger.warning(f"Not enough data for {symbol} inference")
            return None
            
        last_sequence = df[self.feature_columns].iloc[-self.sequence_length:].values
        
        # Add batch dimension: (1, seq_len, features)
        return torch.FloatTensor(last_sequence).unsqueeze(0)
