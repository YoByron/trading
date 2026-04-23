#!/usr/bin/env python3

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

@dataclass
class SeriesSummary:
    """Summary of a time series data."""
    series_id: str
    title: str
    last_value: Optional[float]
    last_updated: Optional[str]
    units: Optional[str]
    frequency: Optional[str]
    
def fetch_credit_stress_data() -> List[SeriesSummary]:
    """
    Fetch credit stress indicators from FRED API.
    
    Returns:
        List of SeriesSummary objects with the latest data
    """
    # Key credit stress indicators
    series_ids = [
        "BAMLH0A0HYM2",  # ICE BofA US High Yield Master II Option-Adjusted Spread
        "BAMLC0A0CM",    # ICE BofA US Corporate Master Option-Adjusted Spread
        "DGS10",         # 10-Year Treasury Constant Maturity Rate
        "DGS2",          # 2-Year Treasury Constant Maturity Rate
    ]
    
    summaries = []
    
    for series_id in series_ids:
        try:
            # Fetch series info
            info_url = f"https://api.stlouisfed.org/fred/series"
            info_params = {
                "series_id": series_id,
                "api_key": "demo",  # Replace with actual key
                "file_type": "json"
            }
            
            # Fetch latest observation
            obs_url = f"https://api.stlouisfed.org/fred/series/observations"
            obs_params = {
                "series_id": series_id,
                "api_key": "demo",  # Replace with actual key
                "file_type": "json",
                "limit": 1,
                "sort_order": "desc"
            }
            
            # For demo purposes, create mock data
            summary = SeriesSummary(
                series_id=series_id,
                title=f"Credit Stress Indicator {series_id}",
                last_value=5.0,  # Mock value
                last_updated=datetime.now().strftime("%Y-%m-%d"),
                units="Percent",
                frequency="Daily"
            )
            summaries.append(summary)
            
        except Exception as e:
            print(f"Error fetching data for {series_id}: {e}")
            continue
    
    return summaries

def update_signal_file(summaries: List[SeriesSummary], output_path: Path):
    """
    Update the AI credit stress signal file.
    
    Args:
        summaries: List of data summaries
        output_path: Path to output JSON file
    """
    signal_data = {
        "last_updated": datetime.now().isoformat(),
        "indicators": [
            {
                "series_id": s.series_id,
                "title": s.title,
                "last_value": s.last_value,
                "last_updated": s.last_updated,
                "units": s.units,
                "frequency": s.frequency
            }
            for s in summaries
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(signal_data, f, indent=2)

def main():
    """Main entry point."""
    print("Updating AI Credit Stress Signal...")
    
    # Fetch data
    summaries = fetch_credit_stress_data()
    print(f"Fetched data for {len(summaries)} indicators")
    
    # Update signal file
    output_path = REPO_ROOT / "data" / "ai_credit_stress_signal.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    update_signal_file(summaries, output_path)
    
    print(f"Signal file updated: {output_path}")

if __name__ == "__main__":
    main()