#!/usr/bin/env python3
"""
Update AI Credit Stress Signal for trading system.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


def evaluate_ai_credit_stress_signal(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate AI credit stress signal based on market data."""
    # Default stress indicators
    stress_indicators = {
        'credit_spreads': market_data.get('credit_spreads', 0.0),
        'volatility_index': market_data.get('vix', 0.0),
        'yield_curve_inversion': market_data.get('yield_inversion', False),
        'liquidity_stress': market_data.get('liquidity_stress', 0.0)
    }
    
    # Calculate stress score (0-100)
    stress_score = 0.0
    
    # Credit spreads component (0-40 points)
    if stress_indicators['credit_spreads'] > 0.05:  # 5% threshold
        stress_score += min(40, stress_indicators['credit_spreads'] * 800)
    
    # Volatility component (0-30 points)
    if stress_indicators['volatility_index'] > 20:
        stress_score += min(30, (stress_indicators['volatility_index'] - 20) * 1.5)
    
    # Yield curve inversion (0-20 points)
    if stress_indicators['yield_curve_inversion']:
        stress_score += 20
    
    # Liquidity stress component (0-10 points)
    stress_score += min(10, stress_indicators['liquidity_stress'] * 10)
    
    # Determine signal level
    if stress_score >= 70:
        signal_level = 'CRITICAL'
    elif stress_score >= 50:
        signal_level = 'HIGH'
    elif stress_score >= 30:
        signal_level = 'MEDIUM'
    else:
        signal_level = 'LOW'
    
    return {
        'signal_level': signal_level,
        'stress_score': min(100, stress_score),
        'indicators': stress_indicators,
        'timestamp': datetime.now().isoformat(),
        'recommendation': get_recommendation(signal_level)
    }


def get_recommendation(signal_level: str) -> str:
    """Get trading recommendation based on signal level."""
    recommendations = {
        'CRITICAL': 'Reduce exposure, increase cash position, hedge credit risk',
        'HIGH': 'Cautious positioning, monitor closely, consider defensive trades',
        'MEDIUM': 'Normal operations with enhanced monitoring',
        'LOW': 'Normal operations, consider opportunistic trades'
    }
    return recommendations.get(signal_level, 'Monitor market conditions')


def update_signal_file(signal_data: Dict[str, Any], output_file: Optional[str] = None) -> Path:
    """Update the AI credit stress signal file."""
    if output_file is None:
        output_file = REPO_ROOT / "data" / "ai_credit_stress_signal.json"
    else:
        output_file = Path(output_file)
    
    # Ensure directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write signal data
    with open(output_file, 'w') as f:
        json.dump(signal_data, f, indent=2)
    
    return output_file


def main():
    """Main entry point for updating AI credit stress signal."""
    # Example market data (in production, this would come from data feeds)
    sample_market_data = {
        'credit_spreads': 0.03,  # 3%
        'vix': 25.0,
        'yield_inversion': False,
        'liquidity_stress': 0.2
    }
    
    print("🔍 Evaluating AI Credit Stress Signal...")
    
    # Evaluate signal
    signal_result = evaluate_ai_credit_stress_signal(sample_market_data)
    
    print(f"📊 Signal Level: {signal_result['signal_level']}")
    print(f"📈 Stress Score: {signal_result['stress_score']:.1f}/100")
    print(f"💡 Recommendation: {signal_result['recommendation']}")
    
    # Update signal file
    signal_file = update_signal_file(signal_result)
    print(f"💾 Signal updated in: {signal_file}")
    
    return signal_result


if __name__ == "__main__":
    main()