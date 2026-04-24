from typing import NamedTuple, List, Dict, Any, Optional
import json
import os
from datetime import datetime

class SeriesSummary(NamedTuple):
    """Summary statistics for a time series."""
    name: str
    count: int
    mean: float
    std: float
    min_value: float
    max_value: float
    last_value: float
    last_updated: str

def calculate_series_summary(data: List[float], name: str) -> SeriesSummary:
    """Calculate summary statistics for a time series.
    
    Args:
        data: List of numeric values
        name: Name of the series
        
    Returns:
        SeriesSummary with calculated statistics
    """
    if not data:
        return SeriesSummary(
            name=name,
            count=0,
            mean=0.0,
            std=0.0,
            min_value=0.0,
            max_value=0.0,
            last_value=0.0,
            last_updated=datetime.now().isoformat()
        )
    
    count = len(data)
    mean = sum(data) / count
    variance = sum((x - mean) ** 2 for x in data) / count
    std = variance ** 0.5
    
    return SeriesSummary(
        name=name,
        count=count,
        mean=round(mean, 4),
        std=round(std, 4),
        min_value=min(data),
        max_value=max(data),
        last_value=data[-1],
        last_updated=datetime.now().isoformat()
    )

def update_stress_signal(
    historical_data: List[float],
    new_value: float,
    threshold_multiplier: float = 2.0
) -> Dict[str, Any]:
    """Update credit stress signal based on new data point.
    
    Args:
        historical_data: Historical stress indicator values
        new_value: New stress indicator value
        threshold_multiplier: Multiplier for stress threshold calculation
        
    Returns:
        Updated signal information
    """
    # Calculate baseline statistics
    if len(historical_data) < 2:
        return {
            "signal": "INSUFFICIENT_DATA",
            "current_value": new_value,
            "threshold": None,
            "stress_level": 0.0,
            "recommendation": "Collect more data points"
        }
    
    summary = calculate_series_summary(historical_data, "stress_indicator")
    threshold = summary.mean + (threshold_multiplier * summary.std)
    
    # Determine stress level
    if new_value > threshold:
        signal = "HIGH_STRESS"
        stress_level = min((new_value - threshold) / summary.std, 10.0)
        recommendation = "Consider reducing position sizes and increasing monitoring"
    elif new_value > summary.mean:
        signal = "MODERATE_STRESS"
        stress_level = (new_value - summary.mean) / summary.std
        recommendation = "Monitor closely for further developments"
    else:
        signal = "LOW_STRESS"
        stress_level = 0.0
        recommendation = "Normal operating conditions"
    
    return {
        "signal": signal,
        "current_value": round(new_value, 4),
        "threshold": round(threshold, 4),
        "stress_level": round(stress_level, 2),
        "recommendation": recommendation,
        "baseline_mean": summary.mean,
        "baseline_std": summary.std,
        "data_points": summary.count
    }

def save_signal_update(signal_data: Dict[str, Any], output_file: str = "credit_stress_signal.json") -> None:
    """Save signal update to file.
    
    Args:
        signal_data: Signal data to save
        output_file: Output file path
    """
    signal_data["last_updated"] = datetime.now().isoformat()
    
    with open(output_file, 'w') as f:
        json.dump(signal_data, f, indent=2)

def load_historical_data(data_file: str = "historical_stress_data.json") -> List[float]:
    """Load historical stress data from file.
    
    Args:
        data_file: Path to historical data file
        
    Returns:
        List of historical stress values
    """
    if not os.path.exists(data_file):
        return []
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        return data.get("stress_values", [])
    except Exception as e:
        print(f"Error loading historical data: {e}")
        return []

def main():
    """Main function to update AI credit stress signal."""
    # Load historical data
    historical_data = load_historical_data()
    
    # Simulate new stress indicator value
    # In practice, this would come from your AI model
    import random
    new_value = random.uniform(0.1, 5.0)
    
    print(f"Processing new stress indicator value: {new_value}")
    
    # Update signal
    signal_data = update_stress_signal(historical_data, new_value)
    
    print(f"Signal: {signal_data['signal']}")
    print(f"Stress Level: {signal_data['stress_level']}")
    print(f"Recommendation: {signal_data['recommendation']}")
    
    # Save updated signal
    save_signal_update(signal_data)
    print("Signal data saved to credit_stress_signal.json")
    
    # Update historical data
    historical_data.append(new_value)
    with open("historical_stress_data.json", 'w') as f:
        json.dump({"stress_values": historical_data}, f)

if __name__ == "__main__":
    main()