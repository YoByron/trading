import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def evaluate_ai_credit_stress_signal(data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate AI credit stress signal based on input data"""
    
    # Default evaluation logic
    stress_level = "LOW"
    confidence = 0.5
    
    if 'market_volatility' in data:
        volatility = data['market_volatility']
        if volatility > 0.8:
            stress_level = "HIGH"
            confidence = 0.9
        elif volatility > 0.5:
            stress_level = "MEDIUM"
            confidence = 0.7
    
    if 'credit_spreads' in data:
        spreads = data['credit_spreads']
        if spreads > 500:
            stress_level = "HIGH"
            confidence = max(confidence, 0.85)
        elif spreads > 200:
            stress_level = "MEDIUM" if stress_level == "LOW" else stress_level
            confidence = max(confidence, 0.65)
    
    return {
        'stress_level': stress_level,
        'confidence': confidence,
        'timestamp': data.get('timestamp', 'unknown'),
        'evaluated_factors': list(data.keys())
    }

def update_signal_from_file(input_file: str, output_file: str = "ai_credit_stress_result.json"):
    """Update AI credit stress signal from input file"""
    
    if not Path(input_file).exists():
        print(f"Input file {input_file} not found")
        return False
    
    with open(input_file, 'r') as f:
        input_data = json.load(f)
    
    result = evaluate_ai_credit_stress_signal(input_data)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"AI credit stress signal updated: {result['stress_level']} (confidence: {result['confidence']})")
    return True

def main():
    """Main entry point for AI credit stress signal update"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update AI Credit Stress Signal')
    parser.add_argument('--input', '-i', default='market_data.json',
                       help='Input file with market data')
    parser.add_argument('--output', '-o', default='ai_credit_stress_result.json',
                       help='Output file for stress signal results')
    
    args = parser.parse_args()
    
    success = update_signal_from_file(args.input, args.output)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())