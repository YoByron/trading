import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np

class CreditStressSignal:
    """AI-driven credit stress signal analysis."""
    
    def __init__(self):
        self.stress_indicators: Dict[str, float] = {}
        self.historical_data: List[Dict[str, Any]] = []
        self.threshold_high = 0.75
        self.threshold_low = 0.25
        
    def update_indicator(self, name: str, value: float, metadata: Optional[Dict] = None):
        """Update a stress indicator value."""
        self.stress_indicators[name] = value
        
        # Record historical data
        record = {
            "timestamp": datetime.now().isoformat(),
            "indicator": name,
            "value": value,
            "metadata": metadata or {}
        }
        self.historical_data.append(record)
        
    def calculate_composite_score(self) -> float:
        """Calculate composite stress score from all indicators."""
        if not self.stress_indicators:
            return 0.0
            
        values = list(self.stress_indicators.values())
        return np.mean(values)
        
    def get_stress_level(self) -> str:
        """Get categorical stress level."""
        score = self.calculate_composite_score()
        
        if score >= self.threshold_high:
            return "HIGH"
        elif score <= self.threshold_low:
            return "LOW"
        else:
            return "MEDIUM"
            
    def get_trending_indicators(self, lookback_hours: int = 24) -> Dict[str, str]:
        """Get trending direction for indicators."""
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        trends = {}
        for indicator in self.stress_indicators.keys():
            # Get recent data for this indicator
            recent_data = [
                record for record in self.historical_data
                if (record["indicator"] == indicator and 
                    datetime.fromisoformat(record["timestamp"]) >= cutoff_time)
            ]
            
            if len(recent_data) >= 2:
                values = [record["value"] for record in recent_data]
                if values[-1] > values[0]:
                    trends[indicator] = "INCREASING"
                elif values[-1] < values[0]:
                    trends[indicator] = "DECREASING"
                else:
                    trends[indicator] = "STABLE"
            else:
                trends[indicator] = "INSUFFICIENT_DATA"
                
        return trends

def evaluate_ai_credit_stress_signal(signal: CreditStressSignal) -> Dict[str, Any]:
    """Evaluate the current state of the credit stress signal."""
    composite_score = signal.calculate_composite_score()
    stress_level = signal.get_stress_level()
    trends = signal.get_trending_indicators()
    
    # Calculate risk metrics
    high_stress_indicators = {
        name: value for name, value in signal.stress_indicators.items()
        if value >= signal.threshold_high
    }
    
    evaluation = {
        "timestamp": datetime.now().isoformat(),
        "composite_score": composite_score,
        "stress_level": stress_level,
        "total_indicators": len(signal.stress_indicators),
        "high_stress_count": len(high_stress_indicators),
        "high_stress_indicators": high_stress_indicators,
        "trends": trends,
        "recommendation": _generate_recommendation(stress_level, trends)
    }
    
    return evaluation

def _generate_recommendation(stress_level: str, trends: Dict[str, str]) -> str:
    """Generate recommendation based on stress level and trends."""
    if stress_level == "HIGH":
        return "REDUCE_EXPOSURE"
    elif stress_level == "LOW":
        increasing_trends = sum(1 for trend in trends.values() if trend == "INCREASING")
        if increasing_trends > len(trends) * 0.5:
            return "MONITOR_CLOSELY"
        else:
            return "MAINTAIN_POSITION"
    else:  # MEDIUM
        return "CAUTIOUS_MONITORING"

def update_signal_with_market_data(signal: CreditStressSignal, market_data: Dict[str, Any]):
    """Update signal with new market data."""
    # Credit spread indicators
    if "credit_spreads" in market_data:
        spread_stress = min(market_data["credit_spreads"] / 500.0, 1.0)  # Normalize
        signal.update_indicator("credit_spread_stress", spread_stress)
    
    # Volatility indicators
    if "volatility" in market_data:
        vol_stress = min(market_data["volatility"] / 50.0, 1.0)  # Normalize
        signal.update_indicator("volatility_stress", vol_stress)
    
    # Default rate indicators
    if "default_rate" in market_data:
        default_stress = min(market_data["default_rate"] / 10.0, 1.0)  # Normalize
        signal.update_indicator("default_rate_stress", default_stress)

def export_signal_data(signal: CreditStressSignal, filepath: str):
    """Export signal data to JSON file."""
    export_data = {
        "current_indicators": signal.stress_indicators,
        "historical_data": signal.historical_data[-100:],  # Last 100 records
        "composite_score": signal.calculate_composite_score(),
        "stress_level": signal.get_stress_level(),
        "export_timestamp": datetime.now().isoformat()
    }
    
    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)