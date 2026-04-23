#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# Add project root to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

@dataclass
class SeriesSummary:
    """Summary of a time series for credit stress signals"""
    name: str
    length: int
    start_date: Optional[str]
    end_date: Optional[str]
    mean_value: float
    std_value: float
    min_value: float
    max_value: float
    missing_values: int

@dataclass
class StressSignalUpdate:
    """Update information for credit stress signals"""
    signal_id: str
    timestamp: str
    value: float
    confidence: float
    source: str

def calculate_series_summary(data: List[float], name: str) -> SeriesSummary:
    """Calculate summary statistics for a data series"""
    if not data:
        return SeriesSummary(
            name=name,
            length=0,
            start_date=None,
            end_date=None,
            mean_value=0.0,
            std_value=0.0,
            min_value=0.0,
            max_value=0.0,
            missing_values=0
        )
    
    import statistics
    
    # Filter out None values
    clean_data = [x for x in data if x is not None]
    missing_count = len(data) - len(clean_data)
    
    if not clean_data:
        return SeriesSummary(
            name=name,
            length=len(data),
            start_date=None,
            end_date=None,
            mean_value=0.0,
            std_value=0.0,
            min_value=0.0,
            max_value=0.0,
            missing_values=missing_count
        )
    
    return SeriesSummary(
        name=name,
        length=len(data),
        start_date=None,  # Would need timestamps to calculate
        end_date=None,
        mean_value=statistics.mean(clean_data),
        std_value=statistics.stdev(clean_data) if len(clean_data) > 1 else 0.0,
        min_value=min(clean_data),
        max_value=max(clean_data),
        missing_values=missing_count
    )

def update_credit_stress_signal(signal_data: Dict[str, Any]) -> StressSignalUpdate:
    """Update a credit stress signal with new data"""
    from datetime import datetime
    
    return StressSignalUpdate(
        signal_id=signal_data.get('signal_id', 'unknown'),
        timestamp=datetime.now().isoformat(),
        value=float(signal_data.get('value', 0.0)),
        confidence=float(signal_data.get('confidence', 0.5)),
        source=signal_data.get('source', 'ai_model')
    )

def validate_signal_update(update: StressSignalUpdate) -> List[str]:
    """Validate a signal update and return any errors"""
    errors = []
    
    if not update.signal_id or update.signal_id == 'unknown':
        errors.append("Signal ID is required")
    
    if update.value < 0 or update.value > 1:
        errors.append("Signal value must be between 0 and 1")
    
    if update.confidence < 0 or update.confidence > 1:
        errors.append("Confidence must be between 0 and 1")
    
    if not update.source:
        errors.append("Source is required")
    
    return errors

def process_signal_batch(signal_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a batch of signal updates"""
    results = {
        "processed": 0,
        "failed": 0,
        "errors": [],
        "updates": []
    }
    
    for signal_data in signal_updates:
        try:
            update = update_credit_stress_signal(signal_data)
            errors = validate_signal_update(update)
            
            if errors:
                results["failed"] += 1
                results["errors"].extend(errors)
            else:
                results["processed"] += 1
                results["updates"].append({
                    "signal_id": update.signal_id,
                    "timestamp": update.timestamp,
                    "value": update.value,
                    "confidence": update.confidence,
                    "source": update.source
                })
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Processing error: {str(e)}")
    
    return results

def main():
    """Main entry point for updating AI credit stress signals"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update AI credit stress signals")
    parser.add_argument("--input", required=True, help="Input file with signal data")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    # Load input data
    with open(args.input, 'r') as f:
        input_data = json.load(f)
    
    # Process signals
    if isinstance(input_data, list):
        results = process_signal_batch(input_data)
    else:
        # Single signal
        results = process_signal_batch([input_data])
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()