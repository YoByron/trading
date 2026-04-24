"""Update AI credit stress signal based on market conditions"""
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

def evaluate_ai_credit_stress_signal(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate AI credit stress signal based on market data"""
    
    # Default signal values
    signal_data = {
        'timestamp': datetime.now().isoformat(),
        'stress_level': 'normal',
        'confidence': 0.0,
        'factors': [],
        'recommendations': []
    }
    
    # Check if market data contains required fields
    required_fields = ['credit_spreads', 'volatility', 'liquidity']
    missing_fields = [field for field in required_fields if field not in market_data]
    
    if missing_fields:
        signal_data['stress_level'] = 'unknown'
        signal_data['factors'].append(f"Missing data fields: {missing_fields}")
        signal_data['recommendations'].append("Ensure all required market data is available")
        return signal_data
    
    # Evaluate stress factors
    stress_score = 0
    factors = []
    
    # Credit spreads analysis
    credit_spreads = market_data.get('credit_spreads', 0)
    if credit_spreads > 300:  # basis points
        stress_score += 2
        factors.append("Elevated credit spreads")
    elif credit_spreads > 200:
        stress_score += 1
        factors.append("Moderately elevated credit spreads")
    
    # Volatility analysis
    volatility = market_data.get('volatility', 0)
    if volatility > 0.25:  # 25%
        stress_score += 2
        factors.append("High volatility")
    elif volatility > 0.15:
        stress_score += 1
        factors.append("Moderate volatility")
    
    # Liquidity analysis
    liquidity = market_data.get('liquidity', 1.0)
    if liquidity < 0.5:
        stress_score += 2
        factors.append("Poor liquidity conditions")
    elif liquidity < 0.7:
        stress_score += 1
        factors.append("Reduced liquidity")
    
    # Determine stress level
    if stress_score >= 4:
        signal_data['stress_level'] = 'high'
        signal_data['confidence'] = 0.8
        signal_data['recommendations'].extend([
            "Reduce credit exposure",
            "Increase cash reserves",
            "Monitor positions closely"
        ])
    elif stress_score >= 2:
        signal_data['stress_level'] = 'moderate'
        signal_data['confidence'] = 0.6
        signal_data['recommendations'].extend([
            "Review credit positions",
            "Consider hedging strategies"
        ])
    else:
        signal_data['stress_level'] = 'normal'
        signal_data['confidence'] = 0.7
        signal_data['recommendations'].append("Maintain current exposure levels")
    
    signal_data['factors'] = factors
    
    return signal_data

def update_signal_database(signal_data: Dict[str, Any]) -> bool:
    """Update the signal in the database"""
    # This would typically connect to a database
    # For now, just return success
    return True

if __name__ == "__main__":
    # Example usage
    sample_market_data = {
        'credit_spreads': 250,
        'volatility': 0.18,
        'liquidity': 0.65
    }
    
    signal = evaluate_ai_credit_stress_signal(sample_market_data)
    print(f"AI Credit Stress Signal: {signal}")
    
    updated = update_signal_database(signal)
    print(f"Database updated: {updated}")