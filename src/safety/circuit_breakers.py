"""
Circuit Breakers - Auto-stop trading on dangerous conditions

Prevents catastrophic losses by automatically halting trading when:
- Daily loss exceeds threshold
- Too many consecutive losses
- Unusual trading patterns
- API errors exceed limit
- Position size anomalies
"""
import logging
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker system to prevent catastrophic losses.
    
    Implements multiple safety mechanisms:
    - Daily loss limit (default: 2% of portfolio)
    - Consecutive loss limit (default: 3 trades)
    - API error limit (default: 5 errors)
    - Position size anomaly detection
    - Emergency kill switch
    """
    
    def __init__(
        self,
        max_daily_loss_pct: float = 0.02,  # 2% max daily loss
        max_consecutive_losses: int = 3,
        max_api_errors: int = 5,
        max_position_size_pct: float = 0.10,  # 10% max per position
        state_file: str = "data/circuit_breaker_state.json"
    ):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.max_api_errors = max_api_errors
        self.max_position_size_pct = max_position_size_pct
        self.state_file = Path(state_file)
        
        # Load state
        self.state = self._load_state()
        self.is_tripped = self.state.get("is_tripped", False)
        
        logger.info(f"Circuit Breaker initialized: max_loss={max_daily_loss_pct:.1%}, "
                   f"max_consec={max_consecutive_losses}, tripped={self.is_tripped}")
    
    def check_before_trade(
        self,
        portfolio_value: float,
        proposed_position_size: float,
        current_pl_today: float
    ) -> Dict[str, Any]:
        """
        Check if trading should be allowed.
        
        Args:
            portfolio_value: Total portfolio value
            proposed_position_size: Proposed trade size
            current_pl_today: Current P/L for today
            
        Returns:
            Dict with 'allowed', 'reason', 'severity'
        """
        checks = []
        
        # Check 1: Kill switch
        if self.is_tripped:
            return {
                "allowed": False,
                "reason": "🚨 CIRCUIT BREAKER TRIPPED - Manual reset required",
                "severity": "CRITICAL",
                "breaker": "KILL_SWITCH"
            }
        
        # Check 2: Daily loss limit
        daily_loss_pct = abs(current_pl_today) / portfolio_value if portfolio_value > 0 else 0
        if current_pl_today < 0 and daily_loss_pct > self.max_daily_loss_pct:
            self._trip_breaker("DAILY_LOSS_LIMIT", f"Daily loss {daily_loss_pct:.2%} exceeds {self.max_daily_loss_pct:.2%}")
            return {
                "allowed": False,
                "reason": f"🛑 Daily loss limit exceeded: {daily_loss_pct:.2%} > {self.max_daily_loss_pct:.2%}",
                "severity": "CRITICAL",
                "breaker": "DAILY_LOSS"
            }
        
        # Check 3: Consecutive losses
        consecutive_losses = self.state.get("consecutive_losses", 0)
        if consecutive_losses >= self.max_consecutive_losses:
            self._trip_breaker("CONSECUTIVE_LOSSES", f"{consecutive_losses} consecutive losses")
            return {
                "allowed": False,
                "reason": f"🛑 Too many consecutive losses: {consecutive_losses}",
                "severity": "CRITICAL",
                "breaker": "CONSECUTIVE_LOSS"
            }
        
        # Check 4: Position size anomaly
        position_pct = proposed_position_size / portfolio_value if portfolio_value > 0 else 0
        if position_pct > self.max_position_size_pct:
            return {
                "allowed": False,
                "reason": f"🛑 Position size too large: {position_pct:.2%} > {self.max_position_size_pct:.2%}",
                "severity": "HIGH",
                "breaker": "POSITION_SIZE"
            }
        
        # Check 5: API error rate
        api_errors_today = self.state.get("api_errors_today", 0)
        if api_errors_today >= self.max_api_errors:
            self._trip_breaker("API_ERRORS", f"{api_errors_today} API errors today")
            return {
                "allowed": False,
                "reason": f"🛑 Too many API errors: {api_errors_today}",
                "severity": "HIGH",
                "breaker": "API_ERROR"
            }
        
        # All checks passed
        return {
            "allowed": True,
            "reason": "✅ All safety checks passed",
            "severity": "NORMAL",
            "checks": {
                "daily_loss": f"{daily_loss_pct:.2%} / {self.max_daily_loss_pct:.2%}",
                "consecutive_losses": f"{consecutive_losses} / {self.max_consecutive_losses}",
                "position_size": f"{position_pct:.2%} / {self.max_position_size_pct:.2%}",
                "api_errors": f"{api_errors_today} / {self.max_api_errors}"
            }
        }
    
    def record_trade_outcome(self, profit_loss: float) -> None:
        """Record trade outcome for consecutive loss tracking."""
        if profit_loss < 0:
            self.state["consecutive_losses"] = self.state.get("consecutive_losses", 0) + 1
            logger.warning(f"Loss recorded: {self.state['consecutive_losses']} consecutive")
        else:
            self.state["consecutive_losses"] = 0  # Reset on win
            logger.info("Win recorded: consecutive losses reset to 0")
        
        self._save_state()
    
    def record_api_error(self) -> None:
        """Record an API error."""
        self.state["api_errors_today"] = self.state.get("api_errors_today", 0) + 1
        logger.warning(f"API error recorded: {self.state['api_errors_today']} today")
        self._save_state()
    
    def reset_daily(self) -> None:
        """Reset daily counters (call at start of day)."""
        today = date.today().isoformat()
        last_reset = self.state.get("last_reset", "")
        
        if last_reset != today:
            self.state["api_errors_today"] = 0
            self.state["last_reset"] = today
            logger.info(f"Daily counters reset for {today}")
            self._save_state()
    
    def _trip_breaker(self, reason_code: str, details: str) -> None:
        """Trip the circuit breaker."""
        self.is_tripped = True
        self.state["is_tripped"] = True
        self.state["trip_reason"] = reason_code
        self.state["trip_details"] = details
        self.state["trip_time"] = datetime.now().isoformat()
        self._save_state()
        
        logger.critical(f"🚨 CIRCUIT BREAKER TRIPPED: {reason_code} - {details}")
    
    def manual_reset(self) -> bool:
        """Manually reset circuit breaker (requires human intervention)."""
        self.is_tripped = False
        self.state["is_tripped"] = False
        self.state["consecutive_losses"] = 0
        self.state["api_errors_today"] = 0
        self.state["reset_by"] = "manual"
        self.state["reset_time"] = datetime.now().isoformat()
        self._save_state()
        
        logger.warning("Circuit breaker manually reset")
        return True
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from disk."""
        if not self.state_file.exists():
            return {
                "is_tripped": False,
                "consecutive_losses": 0,
                "api_errors_today": 0,
                "last_reset": date.today().isoformat()
            }
        
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading circuit breaker state: {e}")
            return {}
    
    def _save_state(self) -> None:
        """Save state to disk."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving circuit breaker state: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "is_tripped": self.is_tripped,
            "consecutive_losses": self.state.get("consecutive_losses", 0),
            "api_errors_today": self.state.get("api_errors_today", 0),
            "last_reset": self.state.get("last_reset", "unknown"),
            "trip_reason": self.state.get("trip_reason", None),
            "trip_details": self.state.get("trip_details", None)
        }

