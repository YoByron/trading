#!/usr/bin/env python3
"""
Lightweight Health Monitor

Quick health checks that can run frequently (every minute).
For use in GitHub Actions scheduled workflows.

Created: Dec 11, 2025
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


class HealthMonitor:
    """Quick health checks for the trading system."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.issues = []
    
    def check_all(self) -> dict:
        """Run all health checks."""
        self.issues = []
        
        checks = {
            "trades_today": self._check_trades_today(),
            "syntax_valid": self._check_syntax(),
            "market_status": self._get_market_status(),
            "last_trade_time": self._get_last_trade_time(),
        }
        
        return {
            "healthy": len(self.issues) == 0,
            "checks": checks,
            "issues": self.issues,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def _check_trades_today(self) -> dict:
        """Check if trades exist for today."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        trades_file = self.data_dir / f"trades_{today}.json"
        
        if not trades_file.exists():
            # Check if market is open
            if self._is_market_open():
                self.issues.append({
                    "type": "no_trades",
                    "severity": "critical",
                    "message": f"No trades file for {today} during market hours",
                })
            return {"exists": False, "count": 0}
        
        try:
            with open(trades_file) as f:
                trades = json.load(f)
            return {"exists": True, "count": len(trades)}
        except Exception:
            return {"exists": True, "count": -1, "error": "corrupt"}
    
    def _check_syntax(self) -> dict:
        """Check critical files have valid syntax."""
        import ast
        
        critical_files = [
            "src/execution/alpaca_executor.py",
            "src/orchestrator/main.py",
        ]
        
        errors = []
        for filepath in critical_files:
            path = Path(filepath)
            if path.exists():
                try:
                    with open(path) as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    errors.append({"file": filepath, "error": str(e)})
                    self.issues.append({
                        "type": "syntax_error",
                        "severity": "critical",
                        "message": f"Syntax error in {filepath}",
                    })
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _get_market_status(self) -> dict:
        """Get current market status."""
        is_open = self._is_market_open()
        now = datetime.now(timezone.utc)
        et_time = now - timedelta(hours=5)
        
        return {
            "is_open": is_open,
            "current_et": et_time.strftime("%H:%M:%S"),
            "day_of_week": et_time.strftime("%A"),
        }
    
    def _get_last_trade_time(self) -> dict:
        """Get timestamp of most recent trade."""
        # Find most recent trades file
        trades_files = sorted(self.data_dir.glob("trades_*.json"), reverse=True)
        
        if not trades_files:
            return {"last_trade": None, "file": None}
        
        try:
            with open(trades_files[0]) as f:
                trades = json.load(f)
            
            if trades:
                last_trade = max(t.get("timestamp", "") for t in trades)
                return {
                    "last_trade": last_trade,
                    "file": str(trades_files[0]),
                }
        except Exception:
            pass
        
        return {"last_trade": None, "file": str(trades_files[0])}
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open."""
        now = datetime.now(timezone.utc)
        et_time = now - timedelta(hours=5)
        
        # Weekday check
        if et_time.weekday() >= 5:
            return False
        
        # Hour check (9:30 AM - 4:00 PM ET)
        if et_time.hour < 9 or (et_time.hour == 9 and et_time.minute < 30):
            return False
        if et_time.hour >= 16:
            return False
        
        return True


def main():
    """CLI entry point."""
    monitor = HealthMonitor()
    result = monitor.check_all()
    
    print(json.dumps(result, indent=2))
    
    # Exit with error if unhealthy
    sys.exit(0 if result["healthy"] else 1)


if __name__ == "__main__":
    main()
