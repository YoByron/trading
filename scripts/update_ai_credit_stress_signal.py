import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List
import json

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class CreditStressSignal:
    signal_strength: float
    risk_indicators: Dict[str, float]
    timestamp: str
    metadata: Dict[str, Any]

def evaluate_ai_credit_stress_signal(market_data: Dict[str, Any] = None) -> CreditStressSignal:
    """Evaluate AI-based credit stress signals from market data."""
    if market_data is None:
        market_data = {
            "credit_spreads": {"investment_grade": 150, "high_yield": 400},
            "treasury_yields": {"2y": 4.5, "10y": 4.8},
            "equity_volatility": 18.5,
            "currency_stress": 0.2
        }
    
    # Calculate risk indicators
    risk_indicators = {}
    
    # Credit spread analysis
    ig_spread = market_data.get("credit_spreads", {}).get("investment_grade", 100)
    hy_spread = market_data.get("credit_spreads", {}).get("high_yield", 300)
    
    risk_indicators["credit_spread_stress"] = min((ig_spread - 100) / 200, 1.0)
    risk_indicators["high_yield_stress"] = min((hy_spread - 300) / 500, 1.0)
    
    # Volatility analysis
    volatility = market_data.get("equity_volatility", 15.0)
    risk_indicators["volatility_stress"] = min((volatility - 15) / 25, 1.0)
    
    # Currency stress
    currency_stress = market_data.get("currency_stress", 0.0)
    risk_indicators["currency_stress"] = min(currency_stress, 1.0)
    
    # Calculate overall signal strength
    signal_strength = sum(risk_indicators.values()) / len(risk_indicators)
    
    return CreditStressSignal(
        signal_strength=signal_strength,
        risk_indicators=risk_indicators,
        timestamp="2024-01-01T00:00:00Z",
        metadata={"model_version": "v1.0", "data_source": "market_feed"}
    )

def update_signal_database(signal: CreditStressSignal) -> bool:
    """Update the credit stress signal in the database."""
    try:
        signal_data = {
            "signal_strength": signal.signal_strength,
            "risk_indicators": signal.risk_indicators,
            "timestamp": signal.timestamp,
            "metadata": signal.metadata
        }
        
        # In a real implementation, this would write to a database
        # For now, we'll just simulate success
        print(f"Updated credit stress signal: {signal.signal_strength:.3f}")
        return True
        
    except Exception as e:
        print(f"Error updating signal database: {e}")
        return False

def main():
    """Main entry point for credit stress signal updates."""
    print("Evaluating AI credit stress signal...")
    
    try:
        signal = evaluate_ai_credit_stress_signal()
        
        print(f"Signal strength: {signal.signal_strength:.3f}")
        print("Risk indicators:")
        for indicator, value in signal.risk_indicators.items():
            print(f"  {indicator}: {value:.3f}")
        
        if update_signal_database(signal):
            print("Signal database updated successfully")
        else:
            print("Failed to update signal database")
            
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()