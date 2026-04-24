"""Update AI credit stress signal."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class CreditStressMetrics:
    """Credit stress signal metrics."""
    stress_level: float
    confidence: float
    timestamp: datetime
    indicators: Dict[str, float]


@dataclass
class SignalEvaluation:
    """Result of signal evaluation."""
    signal_strength: float
    reliability_score: float
    risk_assessment: str
    recommendations: list


def evaluate_ai_credit_stress_signal(
    market_data: Dict[str, Any],
    model_params: Optional[Dict[str, Any]] = None
) -> SignalEvaluation:
    """Evaluate AI credit stress signal based on market data."""
    if not market_data:
        return SignalEvaluation(
            signal_strength=0.0,
            reliability_score=0.0,
            risk_assessment="No data available",
            recommendations=["Obtain market data for analysis"]
        )
    
    # Simplified evaluation logic
    stress_indicators = market_data.get("stress_indicators", {})
    
    # Calculate signal strength (0-1 scale)
    signal_strength = min(1.0, sum(stress_indicators.values()) / len(stress_indicators) if stress_indicators else 0.0)
    
    # Calculate reliability based on data quality
    data_quality = market_data.get("data_quality", 0.5)
    reliability_score = min(1.0, data_quality * signal_strength)
    
    # Assess risk level
    if signal_strength > 0.8:
        risk_assessment = "High stress detected"
    elif signal_strength > 0.5:
        risk_assessment = "Moderate stress detected"
    else:
        risk_assessment = "Low stress levels"
    
    # Generate recommendations
    recommendations = []
    if signal_strength > 0.7:
        recommendations.append("Consider reducing credit exposure")
        recommendations.append("Increase monitoring frequency")
    elif signal_strength > 0.4:
        recommendations.append("Monitor closely for changes")
    else:
        recommendations.append("Continue normal operations")
    
    return SignalEvaluation(
        signal_strength=signal_strength,
        reliability_score=reliability_score,
        risk_assessment=risk_assessment,
        recommendations=recommendations
    )


def update_stress_signal(new_data: Dict[str, Any]) -> CreditStressMetrics:
    """Update the credit stress signal with new data."""
    indicators = new_data.get("indicators", {})
    
    # Calculate overall stress level
    stress_level = sum(indicators.values()) / len(indicators) if indicators else 0.0
    
    # Calculate confidence based on data completeness
    expected_indicators = ["spread_widening", "default_rate", "volatility", "liquidity"]
    available_indicators = len([k for k in expected_indicators if k in indicators])
    confidence = available_indicators / len(expected_indicators)
    
    return CreditStressMetrics(
        stress_level=stress_level,
        confidence=confidence,
        timestamp=datetime.now(),
        indicators=indicators
    )