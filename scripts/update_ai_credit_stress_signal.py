from typing import Dict, Any
import logging


def evaluate_ai_credit_stress_signal(market_data: Dict[str, Any]) -> float:
    """Evaluate AI credit stress signal based on market data."""
    logger = logging.getLogger(__name__)
    
    try:
        # Extract relevant market indicators
        credit_spreads = market_data.get('credit_spreads', 0.0)
        volatility = market_data.get('volatility', 0.0)
        liquidity = market_data.get('liquidity', 1.0)
        
        # Calculate stress signal (0.0 = low stress, 1.0 = high stress)
        stress_signal = min(1.0, max(0.0, 
            (credit_spreads * 0.4) + 
            (volatility * 0.4) + 
            ((1.0 - liquidity) * 0.2)
        ))
        
        logger.info(f"AI credit stress signal calculated: {stress_signal:.4f}")
        return stress_signal
        
    except Exception as e:
        logger.error(f"Error calculating AI credit stress signal: {e}")
        return 0.5  # Default to medium stress on error


def update_ai_credit_stress_signal(signal_value: float) -> bool:
    """Update the AI credit stress signal in the system."""
    logger = logging.getLogger(__name__)
    
    try:
        if not (0.0 <= signal_value <= 1.0):
            logger.error(f"Invalid signal value: {signal_value}. Must be between 0.0 and 1.0")
            return False
        
        # Update signal in system (placeholder implementation)
        logger.info(f"Updated AI credit stress signal to: {signal_value:.4f}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating AI credit stress signal: {e}")
        return False