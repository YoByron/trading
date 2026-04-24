import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

def evaluate_ai_credit_stress_signal(data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate AI credit stress signal based on input data"""
    
    # Extract key metrics
    credit_spread = data.get('credit_spread', 0)
    default_probability = data.get('default_probability', 0)
    market_volatility = data.get('market_volatility', 0)
    
    # Calculate stress score
    stress_score = (credit_spread * 0.4 + 
                   default_probability * 0.4 + 
                   market_volatility * 0.2)
    
    # Determine signal level
    if stress_score > 0.7:
        signal_level = 'HIGH'
    elif stress_score > 0.4:
        signal_level = 'MEDIUM'
    else:
        signal_level = 'LOW'
    
    return {
        'stress_score': stress_score,
        'signal_level': signal_level,
        'timestamp': datetime.now().isoformat(),
        'components': {
            'credit_spread': credit_spread,
            'default_probability': default_probability,
            'market_volatility': market_volatility
        }
    }

def update_credit_stress_database(signal_data: Dict[str, Any]) -> bool:
    """Update the credit stress signal in the database"""
    try:
        # Simulate database update
        print(f"Updating credit stress signal: {signal_data}")
        return True
    except Exception as e:
        print(f"Error updating database: {e}")
        return False

def generate_stress_report(signal_data: Dict[str, Any]) -> str:
    """Generate a human-readable stress report"""
    level = signal_data['signal_level']
    score = signal_data['stress_score']
    
    report = f"""
    AI Credit Stress Signal Report
    ============================
    Signal Level: {level}
    Stress Score: {score:.3f}
    Timestamp: {signal_data['timestamp']}
    
    Component Analysis:
    - Credit Spread: {signal_data['components']['credit_spread']:.3f}
    - Default Probability: {signal_data['components']['default_probability']:.3f}
    - Market Volatility: {signal_data['components']['market_volatility']:.3f}
    """
    
    return report.strip()