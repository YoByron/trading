import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class SeriesSummary:
    series_name: str
    latest_value: float
    previous_value: float
    change: float
    change_percent: float
    last_updated: str
    status: str

@dataclass 
class CreditStressSignal:
    signal_value: float
    confidence: float
    components: Dict[str, float]
    timestamp: str
    metadata: Dict[str, Any]

class AISecondaryTermsCreditStressSignal:
    """AI-powered credit stress signal calculator"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.series_summaries: List[SeriesSummary] = []
        
    def calculate_signal(self, market_data: Dict[str, Any]) -> CreditStressSignal:
        """Calculate the credit stress signal from market data"""
        # Example calculation logic
        components = {
            "credit_spreads": market_data.get("credit_spreads", 0.0),
            "volatility": market_data.get("volatility", 0.0), 
            "liquidity": market_data.get("liquidity", 0.0)
        }
        
        signal_value = np.mean(list(components.values()))
        confidence = min(0.95, max(0.05, 1.0 - np.std(list(components.values()))))
        
        return CreditStressSignal(
            signal_value=signal_value,
            confidence=confidence,
            components=components,
            timestamp=datetime.now().isoformat(),
            metadata={"model_version": "1.0"}
        )
    
    def update_series_summary(self, series_name: str, current_value: float, 
                            previous_value: Optional[float] = None) -> SeriesSummary:
        """Update summary for a data series"""
        if previous_value is None:
            previous_value = current_value * 0.98  # Default assumption
            
        change = current_value - previous_value
        change_percent = (change / previous_value) * 100 if previous_value != 0 else 0
        
        summary = SeriesSummary(
            series_name=series_name,
            latest_value=current_value,
            previous_value=previous_value,
            change=change,
            change_percent=change_percent,
            last_updated=datetime.now().isoformat(),
            status="UPDATED"
        )
        
        self.series_summaries.append(summary)
        return summary

def create_credit_stress_calculator(config: Optional[Dict[str, Any]] = None) -> AISecondaryTermsCreditStressSignal:
    """Factory function to create credit stress calculator"""
    return AISecondaryTermsCreditStressSignal(config)

def main():
    """Main function for updating credit stress signal"""
    calculator = create_credit_stress_calculator()
    
    # Example market data
    market_data = {
        "credit_spreads": 150.0,
        "volatility": 0.25,
        "liquidity": 0.8
    }
    
    signal = calculator.calculate_signal(market_data)
    print(f"Credit stress signal: {signal.signal_value:.3f} (confidence: {signal.confidence:.3f})")

if __name__ == "__main__":
    main()