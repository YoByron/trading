import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

def evaluate_ai_credit_stress_signal(data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate AI credit stress signal based on input data."""
    
    # Default evaluation result
    evaluation = {
        "signal_strength": 0.0,
        "confidence": 0.0,
        "risk_level": "LOW",
        "timestamp": datetime.now().isoformat(),
        "factors": []
    }
    
    try:
        # Extract relevant metrics from data
        credit_metrics = data.get("credit_metrics", {})
        market_data = data.get("market_data", {})
        
        # Calculate signal strength based on available metrics
        signal_factors = []
        
        # Credit spread analysis
        if "credit_spread" in credit_metrics:
            spread = credit_metrics["credit_spread"]
            if spread > 200:  # basis points
                signal_factors.append(0.3)
                evaluation["factors"].append("High credit spreads detected")
            elif spread > 100:
                signal_factors.append(0.1)
                evaluation["factors"].append("Moderate credit spreads")
        
        # Default rate analysis
        if "default_rate" in credit_metrics:
            default_rate = credit_metrics["default_rate"]
            if default_rate > 0.05:  # 5%
                signal_factors.append(0.4)
                evaluation["factors"].append("Elevated default rates")
            elif default_rate > 0.02:  # 2%
                signal_factors.append(0.2)
                evaluation["factors"].append("Moderate default rates")
        
        # Market volatility
        if "volatility" in market_data:
            volatility = market_data["volatility"]
            if volatility > 0.3:  # 30%
                signal_factors.append(0.2)
                evaluation["factors"].append("High market volatility")
        
        # Calculate overall signal strength
        if signal_factors:
            evaluation["signal_strength"] = min(sum(signal_factors), 1.0)
            evaluation["confidence"] = len(signal_factors) / 3.0  # Normalize by max factors
            
            # Determine risk level
            if evaluation["signal_strength"] > 0.7:
                evaluation["risk_level"] = "HIGH"
            elif evaluation["signal_strength"] > 0.3:
                evaluation["risk_level"] = "MEDIUM"
            else:
                evaluation["risk_level"] = "LOW"
    
    except Exception as e:
        evaluation["error"] = str(e)
        evaluation["risk_level"] = "UNKNOWN"
    
    return evaluation

def update_credit_stress_model(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update the credit stress model with new data."""
    
    result = {
        "status": "success",
        "updated_at": datetime.now().isoformat(),
        "model_version": model_data.get("version", "1.0"),
        "changes": []
    }
    
    try:
        # Simulate model update process
        if "training_data" in model_data:
            result["changes"].append("Updated training dataset")
        
        if "parameters" in model_data:
            result["changes"].append("Updated model parameters")
        
        if "weights" in model_data:
            result["changes"].append("Updated model weights")
        
        result["accuracy"] = model_data.get("accuracy", 0.85)
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result