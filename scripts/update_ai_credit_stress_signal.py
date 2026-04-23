#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).parent.parent.absolute()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analytics.ai_credit_stress_signal import AICreditStressSignal


def evaluate_ai_credit_stress_signal():
    """Evaluate AI credit stress signal and update data"""
    signal = AICreditStressSignal()
    
    # Get current signal value
    current_signal = signal.get_current_signal()
    
    # Update historical data
    signal.update_signal()
    
    return {
        'current_signal': current_signal,
        'timestamp': signal.last_updated,
        'status': 'updated'
    }


def main():
    """Main execution function"""
    try:
        result = evaluate_ai_credit_stress_signal()
        print(f"AI Credit Stress Signal Updated: {result}")
        return True
    except Exception as e:
        print(f"Error updating AI Credit Stress Signal: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)