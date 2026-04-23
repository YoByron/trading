from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class CreditStressSignal:
    """AI-driven credit stress signal."""
    timestamp: datetime
    stress_level: float
    confidence: float
    contributing_factors: Dict[str, float]
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not 0 <= self.stress_level <= 1:
            raise ValueError("Stress level must be between 0 and 1")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

class CreditStressAnalyzer:
    """Analyzer for credit stress signals."""
    
    def __init__(self):
        self.model_weights = {
            "market_volatility": 0.3,
            "credit_spreads": 0.4,
            "liquidity_conditions": 0.2,
            "macro_indicators": 0.1
        }
    
    def analyze(self, market_data: Dict[str, Any]) -> CreditStressSignal:
        """Analyze market data to generate credit stress signal."""
        # Simplified stress calculation
        stress_components = {}
        total_stress = 0.0
        
        for factor, weight in self.model_weights.items():
            factor_value = market_data.get(factor, 0.5)
            stress_components[factor] = factor_value
            total_stress += factor_value * weight
        
        return CreditStressSignal(
            timestamp=datetime.now(),
            stress_level=min(1.0, max(0.0, total_stress)),
            confidence=0.8,  # Default confidence
            contributing_factors=stress_components
        )