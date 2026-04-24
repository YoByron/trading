"""Update AI credit stress signal data."""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class SeriesSummary:
    """Summary statistics for a time series."""
    name: str
    count: int
    mean: float
    std: float
    min_value: float
    max_value: float
    last_value: float
    trend: str
    
    @classmethod
    def from_series(cls, series: pd.Series, name: str = None) -> 'SeriesSummary':
        """Create summary from pandas series."""
        if name is None:
            name = series.name or "unnamed"
            
        # Calculate trend (simple slope of last 10 points)
        if len(series) >= 2:
            last_points = series.dropna().tail(min(10, len(series)))
            if len(last_points) >= 2:
                x = np.arange(len(last_points))
                slope = np.polyfit(x, last_points.values, 1)[0]
                if slope > 0.01:
                    trend = "increasing"
                elif slope < -0.01:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "unknown"
        else:
            trend = "insufficient_data"
            
        return cls(
            name=name,
            count=len(series.dropna()),
            mean=float(series.mean()) if not series.empty else 0.0,
            std=float(series.std()) if not series.empty else 0.0,
            min_value=float(series.min()) if not series.empty else 0.0,
            max_value=float(series.max()) if not series.empty else 0.0,
            last_value=float(series.iloc[-1]) if not series.empty else 0.0,
            trend=trend
        )


@dataclass
class CreditStressSignal:
    """AI credit stress signal data structure."""
    timestamp: str
    signal_value: float
    confidence: float
    components: Dict[str, float]
    metadata: Dict[str, Any]


class CreditStressProcessor:
    """Processor for credit stress signals."""
    
    def __init__(self, data_path: str = "data/credit_stress"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
    def load_raw_data(self) -> pd.DataFrame:
        """Load raw credit data."""
        # Placeholder - in real implementation would load from data sources
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'date': dates,
            'credit_spread': np.random.normal(0.05, 0.02, 100),
            'vix': np.random.normal(20, 5, 100),
            'yield_curve': np.random.normal(0.02, 0.01, 100)
        }
        return pd.DataFrame(data)
    
    def calculate_stress_signal(self, data: pd.DataFrame) -> pd.Series:
        """Calculate credit stress signal from raw data."""
        # Simple stress signal calculation
        normalized_spread = (data['credit_spread'] - data['credit_spread'].mean()) / data['credit_spread'].std()
        normalized_vix = (data['vix'] - data['vix'].mean()) / data['vix'].std()
        
        stress_signal = (normalized_spread * 0.6 + normalized_vix * 0.4)
        return stress_signal
    
    def update_signal(self) -> SeriesSummary:
        """Update the credit stress signal."""
        raw_data = self.load_raw_data()
        stress_signal = self.calculate_stress_signal(raw_data)
        
        # Save updated signal
        output_file = self.data_path / "ai_credit_stress_signal.csv"
        result_df = raw_data.copy()
        result_df['ai_stress_signal'] = stress_signal
        result_df.to_csv(output_file, index=False)
        
        return SeriesSummary.from_series(stress_signal, "AI Credit Stress Signal")


def update_ai_credit_stress_signal() -> SeriesSummary:
    """Main function to update AI credit stress signal."""
    processor = CreditStressProcessor()
    summary = processor.update_signal()
    return summary


if __name__ == "__main__":
    summary = update_ai_credit_stress_signal()
    print(f"Updated AI Credit Stress Signal: {summary.name}")
    print(f"Last value: {summary.last_value:.4f}")
    print(f"Trend: {summary.trend}")