import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class SeriesSummary:
    """Summary statistics for a data series"""
    name: str
    count: int
    mean: float
    std: float
    min_val: float
    max_val: float
    last_value: Optional[float] = None
    trend: Optional[str] = None

def calculate_series_summary(data: pd.Series, name: str) -> SeriesSummary:
    """Calculate summary statistics for a data series"""
    return SeriesSummary(
        name=name,
        count=len(data),
        mean=data.mean(),
        std=data.std(),
        min_val=data.min(),
        max_val=data.max(),
        last_value=data.iloc[-1] if len(data) > 0 else None,
        trend="increasing" if len(data) > 1 and data.iloc[-1] > data.iloc[0] else "decreasing"
    )

def update_credit_stress_signal(input_file: str, output_file: str) -> Dict[str, SeriesSummary]:
    """Update AI credit stress signal data"""
    try:
        # Load data
        df = pd.read_csv(input_file)
        
        summaries = {}
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                summaries[column] = calculate_series_summary(df[column], column)
        
        # Save updated data
        df.to_csv(output_file, index=False)
        
        return summaries
    
    except Exception as e:
        print(f"Error updating credit stress signal: {e}")
        return {}

def main():
    """Main function for updating AI credit stress signal"""
    input_file = "data/credit_stress_raw.csv"
    output_file = "data/credit_stress_processed.csv"
    
    summaries = update_credit_stress_signal(input_file, output_file)
    
    for name, summary in summaries.items():
        print(f"{name}: {summary}")

if __name__ == "__main__":
    main()