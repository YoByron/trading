import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class ContextBundle:
    market_data: Dict[str, Any]
    risk_parameters: Dict[str, Any]
    trading_policies: List[str]
    metadata: Dict[str, Any]

def build_context_bundle(market_symbols: List[str] = None) -> ContextBundle:
    """Build a context bundle for agent workflow operations."""
    if market_symbols is None:
        market_symbols = ["SPY", "QQQ", "IWM"]
    
    market_data = {}
    for symbol in market_symbols:
        market_data[symbol] = {
            "price": 100.0,
            "volume": 1000000,
            "volatility": 0.2
        }
    
    risk_parameters = {
        "max_position_size": 0.1,
        "stop_loss": 0.05,
        "max_drawdown": 0.15
    }
    
    trading_policies = [
        "No trading during market close",
        "Maximum position size 10% of portfolio",
        "Stop loss at 5% decline"
    ]
    
    metadata = {
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0",
        "source": "agent_workflow_toolkit"
    }
    
    return ContextBundle(
        market_data=market_data,
        risk_parameters=risk_parameters,
        trading_policies=trading_policies,
        metadata=metadata
    )

def validate_workflow_context(context: ContextBundle) -> bool:
    """Validate that a context bundle has required components."""
    required_fields = ["market_data", "risk_parameters", "trading_policies", "metadata"]
    
    for field in required_fields:
        if not hasattr(context, field):
            return False
    
    # Validate market data structure
    if not isinstance(context.market_data, dict):
        return False
    
    # Validate risk parameters
    required_risk_params = ["max_position_size", "stop_loss", "max_drawdown"]
    for param in required_risk_params:
        if param not in context.risk_parameters:
            return False
    
    return True

def main():
    """Main entry point for workflow toolkit operations."""
    print("Building context bundle...")
    context = build_context_bundle()
    
    if validate_workflow_context(context):
        print("Context bundle validation: PASSED")
        print(f"Market symbols: {list(context.market_data.keys())}")
        print(f"Risk parameters: {context.risk_parameters}")
        print(f"Trading policies: {len(context.trading_policies)} policies loaded")
    else:
        print("Context bundle validation: FAILED")

if __name__ == "__main__":
    main()