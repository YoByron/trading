from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

class SeriesSummary:
    """Summary of a time series analysis."""
    
    def __init__(self, series_name: str, start_date: str, end_date: str):
        self.series_name = series_name
        self.start_date = start_date
        self.end_date = end_date
        self.data_points = 0
        self.mean_value = 0.0
        self.std_deviation = 0.0
        self.min_value = 0.0
        self.max_value = 0.0
        self.trend = "neutral"
        self.volatility = "normal"
        self.quality_score = 1.0
        
    def update_statistics(self, data: List[float]):
        """Update summary statistics from data."""
        if data:
            self.data_points = len(data)
            self.mean_value = sum(data) / len(data)
            self.min_value = min(data)
            self.max_value = max(data)
            
            # Calculate standard deviation
            variance = sum((x - self.mean_value) ** 2 for x in data) / len(data)
            self.std_deviation = variance ** 0.5
            
            # Determine trend (simple slope calculation)
            if len(data) > 1:
                slope = (data[-1] - data[0]) / (len(data) - 1)
                if slope > 0.1:
                    self.trend = "increasing"
                elif slope < -0.1:
                    self.trend = "decreasing"
                else:
                    self.trend = "stable"

class CreditStressSignal:
    """AI-driven credit stress signal analyzer."""
    
    def __init__(self):
        self.signals: List[Dict[str, Any]] = []
        self.current_stress_level = 0.0
        self.last_update = None
        
    def calculate_stress_level(self, market_data: Dict[str, Any]) -> float:
        """Calculate current stress level from market data."""
        # Simple stress calculation based on multiple factors
        stress_factors = []
        
        if 'credit_spreads' in market_data:
            spreads = market_data['credit_spreads']
            if isinstance(spreads, (int, float)):
                stress_factors.append(min(spreads / 100.0, 1.0))
        
        if 'volatility' in market_data:
            vol = market_data['volatility']
            if isinstance(vol, (int, float)):
                stress_factors.append(min(vol / 50.0, 1.0))
        
        if 'liquidity' in market_data:
            liq = market_data['liquidity']
            if isinstance(liq, (int, float)):
                stress_factors.append(max(0, 1.0 - liq / 100.0))
        
        if stress_factors:
            self.current_stress_level = sum(stress_factors) / len(stress_factors)
        else:
            self.current_stress_level = 0.0
            
        return self.current_stress_level
    
    def update_signal(self, market_data: Dict[str, Any]) -> SeriesSummary:
        """Update the credit stress signal with new market data."""
        stress_level = self.calculate_stress_level(market_data)
        
        signal_entry = {
            'timestamp': datetime.now().isoformat(),
            'stress_level': stress_level,
            'market_data': market_data
        }
        
        self.signals.append(signal_entry)
        self.last_update = datetime.now()
        
        # Create summary
        summary = SeriesSummary(
            series_name="AI Credit Stress Signal",
            start_date=self.signals[0]['timestamp'] if self.signals else signal_entry['timestamp'],
            end_date=signal_entry['timestamp']
        )
        
        # Update statistics with recent stress levels
        recent_levels = [s['stress_level'] for s in self.signals[-100:]]  # Last 100 points
        summary.update_statistics(recent_levels)
        
        return summary
    
    def get_signal_summary(self) -> Optional[SeriesSummary]:
        """Get a summary of the current signal state."""
        if not self.signals:
            return None
            
        summary = SeriesSummary(
            series_name="AI Credit Stress Signal",
            start_date=self.signals[0]['timestamp'],
            end_date=self.signals[-1]['timestamp']
        )
        
        stress_levels = [s['stress_level'] for s in self.signals]
        summary.update_statistics(stress_levels)
        
        return summary

def update_ai_credit_stress_signal(market_data: Dict[str, Any]) -> SeriesSummary:
    """Update the AI credit stress signal with new market data."""
    signal = CreditStressSignal()
    return signal.update_signal(market_data)