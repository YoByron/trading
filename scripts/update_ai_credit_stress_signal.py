import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StressSignal:
    signal_id: str
    value: float
    confidence: float
    timestamp: datetime
    factors: Dict[str, float]


@dataclass
class CreditStressEvaluation:
    overall_stress: float
    signals: List[StressSignal]
    risk_level: str
    recommendations: List[str]


def calculate_stress_metrics(credit_data: Dict[str, float]) -> Dict[str, float]:
    metrics = {}
    
    if "default_rate" in credit_data:
        metrics["default_stress"] = min(credit_data["default_rate"] * 10, 1.0)
    
    if "spread_widening" in credit_data:
        metrics["spread_stress"] = min(credit_data["spread_widening"] / 100, 1.0)
    
    if "liquidity_ratio" in credit_data:
        metrics["liquidity_stress"] = max(0, 1 - credit_data["liquidity_ratio"])
    
    return metrics


def evaluate_ai_credit_stress_signal(market_data: Dict[str, Any]) -> CreditStressEvaluation:
    credit_data = market_data.get("credit", {})
    stress_metrics = calculate_stress_metrics(credit_data)
    
    signals = []
    for metric_name, value in stress_metrics.items():
        signal = StressSignal(
            signal_id=f"ai_credit_{metric_name}",
            value=value,
            confidence=0.8,
            timestamp=datetime.now(),
            factors={metric_name: value}
        )
        signals.append(signal)
    
    overall_stress = np.mean(list(stress_metrics.values())) if stress_metrics else 0
    
    if overall_stress > 0.7:
        risk_level = "HIGH"
        recommendations = ["Reduce credit exposure", "Increase cash reserves"]
    elif overall_stress > 0.4:
        risk_level = "MEDIUM" 
        recommendations = ["Monitor positions closely", "Prepare contingency plans"]
    else:
        risk_level = "LOW"
        recommendations = ["Maintain current strategy"]
    
    return CreditStressEvaluation(
        overall_stress=overall_stress,
        signals=signals,
        risk_level=risk_level,
        recommendations=recommendations
    )


def update_signal_database(evaluation: CreditStressEvaluation) -> bool:
    try:
        print(f"Updating stress signals: {len(evaluation.signals)} signals")
        return True
    except Exception:
        return False


def main():
    sample_data = {
        "credit": {
            "default_rate": 0.05,
            "spread_widening": 150,
            "liquidity_ratio": 0.7
        }
    }
    
    evaluation = evaluate_ai_credit_stress_signal(sample_data)
    print(f"Overall Stress: {evaluation.overall_stress:.2f}")
    print(f"Risk Level: {evaluation.risk_level}")
    print(f"Signals: {len(evaluation.signals)}")
    
    update_signal_database(evaluation)


if __name__ == "__main__":
    main()