import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.analytics.ai_credit_stress_signal import (
    CreditStressAnalyzer,
    CreditStressSignal,
)

# Try to import requests, make it optional
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def fetch_market_data() -> Optional[Dict[str, Any]]:
    """Fetch market data for credit stress analysis"""
    if not HAS_REQUESTS:
        print("Warning: requests module not available, using mock data")
        return {
            "vix": 20.5,
            "credit_spreads": 150,
            "treasury_yield": 4.5,
            "timestamp": datetime.now().isoformat()
        }
    
    # In a real implementation, this would fetch from actual APIs
    return {
        "vix": 20.5,
        "credit_spreads": 150,
        "treasury_yield": 4.5,
        "timestamp": datetime.now().isoformat()
    }

def update_credit_stress_signal():
    """Update the AI credit stress signal"""
    analyzer = CreditStressAnalyzer()
    
    # Fetch current market data
    market_data = fetch_market_data()
    if not market_data:
        print("Failed to fetch market data")
        return False
    
    # Analyze credit stress
    try:
        signal = analyzer.analyze_credit_stress(market_data)
        
        # Save signal to file
        output_path = REPO_ROOT / "data" / "credit_stress_signal.json"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(signal.to_dict(), f, indent=2)
        
        print(f"Credit stress signal updated: {signal.stress_level}")
        return True
    
    except Exception as e:
        print(f"Error updating credit stress signal: {str(e)}")
        return False

def main():
    """Main function"""
    print("Updating AI credit stress signal...")
    success = update_credit_stress_signal()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)