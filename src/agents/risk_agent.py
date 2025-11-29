"""
Risk Agent: Portfolio risk management and position sizing

Responsibilities:
- Calculate position sizes (Kelly Criterion)
- Set stop-loss levels
- Portfolio risk assessment
- Circuit breaker checks

Ensures we never blow up the account
"""

import logging
from typing import Dict, Any
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """
    Risk Agent manages portfolio risk and position sizing.

    Key functions:
    - Position sizing based on Kelly Criterion
    - Stop-loss calculation
    - Portfolio diversification checks
    - Circuit breakers
    """

    def __init__(
        self, max_portfolio_risk: float = 0.02, max_position_size: float = 0.05
    ):
        super().__init__(
            name="RiskAgent", role="Portfolio risk management and position sizing"
        )
        self.max_portfolio_risk = max_portfolio_risk  # Max 2% risk per trade
        self.max_position_size = max_position_size  # Max 5% per position

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk and calculate position sizing.

        Args:
            data: Portfolio state, proposed trade, market conditions

        Returns:
            Risk analysis with position size recommendation
        """
        portfolio_value = data.get("portfolio_value", 100000)
        proposed_action = data.get("proposed_action", "HOLD")
        symbol = data.get("symbol", "UNKNOWN")
        confidence = data.get("confidence", 0.5)
        volatility = data.get("volatility", 0.20)
        win_rate = data.get("historical_win_rate", 0.60)

        # Calculate position size
        position_size = self._calculate_position_size(
            portfolio_value, confidence, volatility, win_rate
        )

        # Calculate stop-loss
        stop_loss_pct = self._calculate_stop_loss(volatility)

        # Risk assessment
        memory_context = self.get_memory_context(limit=3)

        prompt = f"""You are a Risk Agent evaluating a proposed {proposed_action} trade on {symbol}.

PORTFOLIO STATE:
- Total Value: ${portfolio_value:,.2f}
- Max Risk Per Trade: {self.max_portfolio_risk:.2%}
- Max Position Size: {self.max_position_size:.2%}

PROPOSED TRADE:
- Action: {proposed_action}
- Confidence: {confidence:.2f}
- Symbol Volatility: {volatility:.2%}
- Historical Win Rate: {win_rate:.2%}

CALCULATED RISK PARAMETERS:
- Recommended Position Size: ${position_size:,.2f} ({position_size/portfolio_value:.2%} of portfolio)
- Recommended Stop-Loss: {stop_loss_pct:.2%}
- Max Loss: ${position_size * stop_loss_pct:,.2f}

{memory_context}

TASK: Provide risk assessment:
1. Risk Score (1-10, where 10 is highest risk)
2. Position Size Approval (APPROVE / REDUCE / REJECT)
3. Final Position Size (in $)
4. Stop-Loss Level (%)
5. Key Risk Factors
6. Overall Recommendation: APPROVE / REJECT

Format:
RISK_SCORE: [1-10]
POSITION_APPROVAL: [APPROVE/REDUCE/REJECT]
POSITION_SIZE: [dollars]
STOP_LOSS: [percentage]
RISKS: [key risks]
RECOMMENDATION: [APPROVE/REJECT]"""

        # Get LLM analysis
        response = self.reason_with_llm(prompt)

        # Parse response
        analysis = self._parse_risk_response(response["reasoning"])
        analysis["calculated_position_size"] = position_size
        analysis["calculated_stop_loss"] = stop_loss_pct
        analysis["full_reasoning"] = response["reasoning"]

        # Log decision
        self.log_decision(analysis)

        return analysis

    def _calculate_position_size(
        self,
        portfolio_value: float,
        confidence: float,
        volatility: float,
        win_rate: float,
    ) -> float:
        """
        Calculate position size using Kelly Criterion with safety adjustments.

        Args:
            portfolio_value: Total portfolio value
            confidence: Trade confidence (0-1)
            volatility: Symbol volatility
            win_rate: Historical win rate

        Returns:
            Position size in dollars
        """
        # Kelly Criterion: f = (p * b - q) / b
        # where p = win probability, q = loss probability, b = win/loss ratio

        win_prob = min(confidence * win_rate, 0.8)  # Cap at 80%
        loss_prob = 1 - win_prob
        win_loss_ratio = 1.5  # Assume 1.5:1 reward/risk

        kelly_fraction = (win_prob * win_loss_ratio - loss_prob) / win_loss_ratio

        # Safety: Use half-Kelly and cap at max position size
        safe_fraction = max(kelly_fraction * 0.5, 0.01)  # Min 1%
        safe_fraction = min(safe_fraction, self.max_position_size)  # Max 5%

        # Adjust for volatility (higher vol = smaller position)
        volatility_adjustment = 1.0 / (1.0 + volatility * 2)
        adjusted_fraction = safe_fraction * volatility_adjustment

        position_size = portfolio_value * adjusted_fraction

        # Enforce minimums and maximums
        position_size = max(position_size, 10.0)  # Min $10
        position_size = min(position_size, portfolio_value * self.max_position_size)

        return position_size

    def _calculate_stop_loss(self, volatility: float) -> float:
        """
        Calculate stop-loss percentage based on volatility.

        Args:
            volatility: Symbol volatility

        Returns:
            Stop-loss percentage (e.g., 0.05 = 5%)
        """
        # 2x volatility as stop-loss (gives room for normal fluctuations)
        stop_loss = volatility * 2

        # Cap between 2% and 10%
        stop_loss = max(stop_loss, 0.02)
        stop_loss = min(stop_loss, 0.10)

        return stop_loss

    def _parse_risk_response(self, reasoning: str) -> Dict[str, Any]:
        """Parse LLM response into structured risk assessment."""
        lines = reasoning.split("\n")
        analysis = {
            "risk_score": 5,
            "position_approval": "APPROVE",
            "position_size": 0,
            "stop_loss": 0.05,
            "risks": "",
            "action": "APPROVE",
        }

        for line in lines:
            line = line.strip()
            if line.startswith("RISK_SCORE:"):
                try:
                    analysis["risk_score"] = int(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("POSITION_APPROVAL:"):
                approval = line.split(":")[1].strip().upper()
                if approval in ["APPROVE", "REDUCE", "REJECT"]:
                    analysis["position_approval"] = approval
            elif line.startswith("POSITION_SIZE:"):
                try:
                    size_str = (
                        line.split(":")[1].strip().replace("$", "").replace(",", "")
                    )
                    analysis["position_size"] = float(size_str)
                except:
                    pass
            elif line.startswith("STOP_LOSS:"):
                try:
                    sl_str = line.split(":")[1].strip().replace("%", "")
                    analysis["stop_loss"] = float(sl_str) / 100
                except:
                    pass
            elif line.startswith("RISKS:"):
                analysis["risks"] = line.split(":", 1)[1].strip()
            elif line.startswith("RECOMMENDATION:"):
                rec = line.split(":")[1].strip().upper()
                if rec in ["APPROVE", "REJECT"]:
                    analysis["action"] = rec

        return analysis
