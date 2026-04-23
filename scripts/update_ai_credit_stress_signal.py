#!/usr/bin/env python3
"""AI Credit Stress Signal updater for trading system."""

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class SeriesSummary:
    """Summary statistics for a time series."""
    series_id: str
    title: str
    current_value: float
    previous_value: float
    change: float
    change_percent: float
    last_updated: str


def fetch_fred_data(series_id: str, api_key: str, days_back: int = 30) -> Optional[pd.DataFrame]:
    """Fetch data from FRED API."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' not in data:
            return None
            
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.dropna(subset=['value'])
        
        return df.sort_values('date')
        
    except Exception as e:
        print(f"Error fetching data for {series_id}: {e}")
        return None


def calculate_stress_signal(credit_spreads: Dict[str, pd.DataFrame]) -> float:
    """Calculate AI credit stress signal from credit spread data."""
    if not credit_spreads:
        return 0.0
    
    stress_components = []
    
    for series_id, df in credit_spreads.items():
        if len(df) < 2:
            continue
            
        current_value = df.iloc[-1]['value']
        previous_value = df.iloc[-2]['value']
        
        if previous_value > 0:
            change_percent = ((current_value - previous_value) / previous_value) * 100
            stress_components.append(change_percent)
    
    if not stress_components:
        return 0.0
    
    # Calculate weighted average stress signal
    return sum(stress_components) / len(stress_components)


def main():
    """Main function to update AI credit stress signal."""
    print("🔍 Updating AI Credit Stress Signal...")
    
    # Mock API key for testing
    api_key = "mock_api_key"
    
    # Credit spread series to monitor
    credit_series = {
        'DGS10': 'Treasury 10-Year',
        'DGS2': 'Treasury 2-Year',
        'BAMLH0A0HYM2': 'High Yield Credit Spread'
    }
    
    # Fetch data for all series
    credit_data = {}
    summaries = []
    
    for series_id, title in credit_series.items():
        df = fetch_fred_data(series_id, api_key)
        if df is not None and len(df) >= 2:
            credit_data[series_id] = df
            
            current_value = df.iloc[-1]['value']
            previous_value = df.iloc[-2]['value']
            change = current_value - previous_value
            change_percent = (change / previous_value) * 100 if previous_value != 0 else 0
            
            summaries.append(SeriesSummary(
                series_id=series_id,
                title=title,
                current_value=current_value,
                previous_value=previous_value,
                change=change,
                change_percent=change_percent,
                last_updated=df.iloc[-1]['date'].strftime('%Y-%m-%d')
            ))
    
    # Calculate stress signal
    stress_signal = calculate_stress_signal(credit_data)
    
    # Output results
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'stress_signal': stress_signal,
        'series_summaries': [
            {
                'series_id': s.series_id,
                'title': s.title,
                'current_value': s.current_value,
                'previous_value': s.previous_value,
                'change': s.change,
                'change_percent': s.change_percent,
                'last_updated': s.last_updated
            }
            for s in summaries
        ]
    }
    
    output_file = REPO_ROOT / "data" / "ai_credit_stress_signal.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ AI Credit Stress Signal updated: {stress_signal:.2f}")
    print(f"   Output saved to: {output_file}")


if __name__ == "__main__":
    main()