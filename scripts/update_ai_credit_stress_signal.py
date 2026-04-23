#!/usr/bin/env python3
"""
AI Credit Stress Signal Update Script
Updates and evaluates AI-based credit stress indicators.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

def evaluate_ai_credit_stress_signal(market_data: Dict) -> Dict:
    """
    Evaluate AI credit stress signal based on market data
    
    Args:
        market_data: Dictionary containing market indicators
        
    Returns:
        Dictionary with stress signal evaluation results
    """
    stress_indicators = {
        'credit_spreads': market_data.get('credit_spreads', 0),
        'volatility_index': market_data.get('vix', 0),
        'treasury_yield_curve': market_data.get('yield_curve_slope', 0),
        'corporate_bond_flows': market_data.get('bond_flows', 0)
    }
    
    # Simple stress scoring algorithm
    stress_score = 0
    
    # Credit spreads factor
    if stress_indicators['credit_spreads'] > 500:  # basis points
        stress_score += 0.3
    elif stress_indicators['credit_spreads'] > 300:
        stress_score += 0.2
    elif stress_indicators['credit_spreads'] > 200:
        stress_score += 0.1
    
    # Volatility factor
    if stress_indicators['volatility_index'] > 30:
        stress_score += 0.25
    elif stress_indicators['volatility_index'] > 20:
        stress_score += 0.15
    
    # Yield curve factor (inverted curve indicates stress)
    if stress_indicators['treasury_yield_curve'] < 0:
        stress_score += 0.25
    elif stress_indicators['treasury_yield_curve'] < 50:  # basis points
        stress_score += 0.15
    
    # Bond flows factor (negative flows indicate stress)
    if stress_indicators['corporate_bond_flows'] < -1000000:  # $1M outflow
        stress_score += 0.2
    elif stress_indicators['corporate_bond_flows'] < -500000:
        stress_score += 0.1
    
    # Normalize to 0-1 scale
    stress_score = min(stress_score, 1.0)
    
    # Determine stress level
    if stress_score >= 0.7:
        stress_level = "HIGH"
    elif stress_score >= 0.4:
        stress_level = "MEDIUM"
    elif stress_score >= 0.2:
        stress_level = "LOW"
    else:
        stress_level = "MINIMAL"
    
    return {
        'stress_score': stress_score,
        'stress_level': stress_level,
        'indicators': stress_indicators,
        'timestamp': datetime.now().isoformat(),
        'signal_strength': stress_score * 100  # Convert to percentage
    }

def update_stress_signal_file(signal_data: Dict, output_path: str = "data/ai_credit_stress.json"):
    """Update the stress signal file with new data"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load existing data if file exists
    historical_data = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    historical_data = existing_data
                elif isinstance(existing_data, dict) and 'history' in existing_data:
                    historical_data = existing_data['history']
        except (json.JSONDecodeError, KeyError):
            historical_data = []
    
    # Add new signal to history
    historical_data.append(signal_data)
    
    # Keep only last 100 entries
    if len(historical_data) > 100:
        historical_data = historical_data[-100:]
    
    # Prepare output data
    output_data = {
        'current_signal': signal_data,
        'history': historical_data,
        'last_updated': datetime.now().isoformat()
    }
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return output_path

def fetch_market_data() -> Dict:
    """Fetch current market data (placeholder implementation)"""
    # In a real implementation, this would fetch from market data APIs
    # For now, return mock data
    return {
        'credit_spreads': 280,  # basis points
        'vix': 22.5,           # VIX volatility index
        'yield_curve_slope': 45,  # basis points (10Y - 2Y)
        'bond_flows': -250000   # corporate bond flows
    }

def main():
    """Main function to update AI credit stress signal"""
    print("Updating AI Credit Stress Signal...")
    
    # Fetch current market data
    market_data = fetch_market_data()
    print(f"Market data fetched: {market_data}")
    
    # Evaluate stress signal
    signal_result = evaluate_ai_credit_stress_signal(market_data)
    print(f"Stress evaluation: {signal_result['stress_level']} ({signal_result['stress_score']:.2f})")
    
    # Update signal file
    output_path = update_stress_signal_file(signal_result)
    print(f"Signal updated and saved to: {output_path}")
    
    # Output summary
    print("\nStress Signal Summary:")
    print(f"  Level: {signal_result['stress_level']}")
    print(f"  Score: {signal_result['stress_score']:.3f}")
    print(f"  Strength: {signal_result['signal_strength']:.1f}%")
    print(f"  Timestamp: {signal_result['timestamp']}")
    
    return signal_result

if __name__ == "__main__":
    main()