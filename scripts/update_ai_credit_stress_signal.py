#!/usr/bin/env python3
"""
Update AI credit stress signal for trading system.
"""
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


@dataclass
class SeriesSummary:
    """Summary of a time series for credit stress analysis."""
    series_id: str
    count: int
    mean: float
    std: float
    min_value: float
    max_value: float
    last_value: float
    trend: str  # 'up', 'down', 'stable'


class CreditStressSignalUpdater:
    """Updates credit stress signals for the AI trading system."""
    
    def __init__(self):
        self.data_path = REPO_ROOT / "data" / "credit_stress"
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.signals_file = self.data_path / "stress_signals.json"
    
    def generate_series_summary(self, series_id: str, data: List[float]) -> SeriesSummary:
        """Generate summary statistics for a data series."""
        if not data:
            return SeriesSummary(
                series_id=series_id,
                count=0,
                mean=0.0,
                std=0.0,
                min_value=0.0,
                max_value=0.0,
                last_value=0.0,
                trend='stable'
            )
        
        import statistics
        
        count = len(data)
        mean_val = statistics.mean(data)
        std_val = statistics.stdev(data) if count > 1 else 0.0
        min_val = min(data)
        max_val = max(data)
        last_val = data[-1]
        
        # Simple trend detection
        if count >= 2:
            if data[-1] > data[-2]:
                trend = 'up'
            elif data[-1] < data[-2]:
                trend = 'down'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return SeriesSummary(
            series_id=series_id,
            count=count,
            mean=mean_val,
            std=std_val,
            min_value=min_val,
            max_value=max_val,
            last_value=last_val,
            trend=trend
        )
    
    def update_stress_signals(self) -> bool:
        """Update credit stress signals."""
        try:
            # Mock data for demonstration
            mock_data = {
                "credit_spreads": [1.2, 1.3, 1.4, 1.5, 1.6],
                "default_rates": [0.02, 0.025, 0.03, 0.028, 0.032],
                "liquidity_index": [0.8, 0.75, 0.7, 0.72, 0.68]
            }
            
            summaries = {}
            for series_id, data in mock_data.items():
                summary = self.generate_series_summary(series_id, data)
                summaries[series_id] = {
                    "series_id": summary.series_id,
                    "count": summary.count,
                    "mean": summary.mean,
                    "std": summary.std,
                    "min_value": summary.min_value,
                    "max_value": summary.max_value,
                    "last_value": summary.last_value,
                    "trend": summary.trend
                }
            
            # Save to file
            with open(self.signals_file, 'w') as f:
                json.dump(summaries, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error updating stress signals: {e}")
            return False


def main():
    """Main function to update credit stress signals."""
    updater = CreditStressSignalUpdater()
    success = updater.update_stress_signals()
    
    if success:
        print("✅ Credit stress signals updated successfully")
    else:
        print("❌ Failed to update credit stress signals")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)