import json
import requests
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime

@dataclass
class SeriesSummary:
    symbol: str
    current_value: float
    change_percent: float
    last_updated: str
    status: str

@dataclass
class StressSignal:
    level: str
    confidence: float
    indicators: List[str]
    timestamp: str

def fetch_credit_data() -> Dict[str, Any]:
    """Fetch credit market data from external sources."""
    # Mock implementation - in real scenario, this would fetch from actual APIs
    mock_data = {
        'high_yield_spread': 450.5,
        'investment_grade_spread': 125.2,
        'volatility_index': 23.8,
        'treasury_10y': 4.25,
        'timestamp': datetime.now().isoformat()
    }
    return mock_data

def calculate_stress_level(data: Dict[str, Any]) -> StressSignal:
    """Calculate stress signal based on credit market data."""
    hy_spread = data.get('high_yield_spread', 0)
    ig_spread = data.get('investment_grade_spread', 0)
    volatility = data.get('volatility_index', 0)
    
    indicators = []
    stress_score = 0
    
    # High yield spread analysis
    if hy_spread > 500:
        stress_score += 3
        indicators.append("High yield spreads elevated")
    elif hy_spread > 400:
        stress_score += 2
        indicators.append("High yield spreads moderately elevated")
    
    # Investment grade spread analysis
    if ig_spread > 150:
        stress_score += 2
        indicators.append("Investment grade spreads widening")
    elif ig_spread > 120:
        stress_score += 1
        indicators.append("Investment grade spreads slightly elevated")
    
    # Volatility analysis
    if volatility > 30:
        stress_score += 2
        indicators.append("Market volatility high")
    elif volatility > 20:
        stress_score += 1
        indicators.append("Market volatility elevated")
    
    # Determine stress level
    if stress_score >= 5:
        level = "HIGH"
        confidence = 0.8
    elif stress_score >= 3:
        level = "MEDIUM"
        confidence = 0.7
    else:
        level = "LOW"
        confidence = 0.6
    
    return StressSignal(
        level=level,
        confidence=confidence,
        indicators=indicators,
        timestamp=data.get('timestamp', datetime.now().isoformat())
    )

def update_signal_database(signal: StressSignal) -> bool:
    """Update the stress signal in the database."""
    # Mock implementation - would connect to actual database
    try:
        # Simulate database update
        print(f"Updated stress signal: {signal.level} (confidence: {signal.confidence})")
        return True
    except Exception as e:
        print(f"Failed to update database: {e}")
        return False

def generate_series_summary(symbol: str, data: Dict[str, Any]) -> SeriesSummary:
    """Generate summary for a specific financial series."""
    current_value = data.get('current_value', 0.0)
    previous_value = data.get('previous_value', current_value)
    
    change_percent = 0.0
    if previous_value != 0:
        change_percent = ((current_value - previous_value) / previous_value) * 100
    
    return SeriesSummary(
        symbol=symbol,
        current_value=current_value,
        change_percent=change_percent,
        last_updated=datetime.now().isoformat(),
        status="ACTIVE"
    )