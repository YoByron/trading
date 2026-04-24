from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

class SeriesSummary:
    def __init__(self, name: str, data: List[float]):
        self.name = name
        self.data = data
        self.count = len(data)
        self.mean = np.mean(data) if data else 0
        self.std = np.std(data) if data else 0
        self.min_val = min(data) if data else 0
        self.max_val = max(data) if data else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            'name': self.name,
            'count': self.count,
            'mean': self.mean,
            'std': self.std,
            'min': self.min_val,
            'max': self.max_val
        }

class CreditStressSignalUpdater:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.signals = {}
    
    def update_signal(self, symbol: str, stress_level: float, confidence: float) -> bool:
        """Update credit stress signal for a symbol."""
        try:
            self.signals[symbol] = {
                'stress_level': stress_level,
                'confidence': confidence,
                'timestamp': datetime.now(),
                'status': 'updated'
            }
            self.logger.info(f"Updated credit stress signal for {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update signal: {e}")
            return False
    
    def get_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get credit stress signal for a symbol."""
        return self.signals.get(symbol)
    
    def calculate_portfolio_stress(self, positions: Dict[str, float]) -> float:
        """Calculate portfolio-level credit stress."""
        total_stress = 0.0
        total_weight = 0.0
        
        for symbol, weight in positions.items():
            if symbol in self.signals:
                signal = self.signals[symbol]
                stress_contribution = signal['stress_level'] * weight * signal['confidence']
                total_stress += stress_contribution
                total_weight += weight
        
        return total_stress / total_weight if total_weight > 0 else 0.0

def generate_stress_summary(signals: Dict[str, Any]) -> SeriesSummary:
    """Generate summary statistics for credit stress signals."""
    stress_levels = [signal['stress_level'] for signal in signals.values()]
    return SeriesSummary("Credit Stress Levels", stress_levels)