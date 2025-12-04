"""
Programmatic Tool Calling (PTC) Orchestrator

Implements Anthropic's PTC pattern for efficient multi-tool orchestration.
Reference: https://www.anthropic.com/engineering/code-execution-with-mcp

Benefits:
- 37% token reduction on complex tasks
- ~19x fewer inference passes (latency reduction)
- 4.7% accuracy improvement on GIA benchmarks
- Intermediate results stay in sandbox, not context window

Usage:
    orchestrator = PTCOrchestrator()
    result = orchestrator.execute_trading_workflow(symbol="SPY", data=market_data)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from anthropic import Anthropic

from src.utils.self_healing import get_anthropic_api_key

logger = logging.getLogger(__name__)

# Beta header for advanced tool use (PTC)
PTC_BETA_HEADER = "advanced-tool-use-2025-11-20"


@dataclass
class PTCToolDefinition:
    """Definition for a tool available in PTC execution."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]


@dataclass
class PTCExecutionResult:
    """Result from a PTC execution."""

    success: bool
    final_output: Any
    code_executed: str
    token_usage: dict[str, int] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    tools_invoked: list[str] = field(default_factory=list)
    error: Optional[str] = None


class PTCOrchestrator:
    """
    Programmatic Tool Calling Orchestrator.

    Enables Claude to write code that orchestrates multiple tools,
    keeping intermediate results in sandbox rather than context window.

    Key Patterns:
    1. Define tools with handlers
    2. Claude writes orchestration code
    3. Code executes in sandbox with tool access
    4. Only final result returns to context
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        enable_code_execution: bool = True,
    ):
        self.client = Anthropic(api_key=get_anthropic_api_key())
        self.model = model
        self.enable_code_execution = enable_code_execution
        self.tools: dict[str, PTCToolDefinition] = {}
        self._register_trading_tools()

    def _register_trading_tools(self) -> None:
        """Register built-in trading tools for PTC."""
        # These tools will be available in the code execution sandbox
        self.register_tool(
            PTCToolDefinition(
                name="fetch_market_data",
                description="Fetch real-time market data for a symbol",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"},
                        "timeframe": {
                            "type": "string",
                            "enum": ["1m", "5m", "15m", "1h", "1d"],
                        },
                    },
                    "required": ["symbol"],
                },
                handler=self._fetch_market_data_handler,
            )
        )

        self.register_tool(
            PTCToolDefinition(
                name="analyze_signals",
                description="Analyze technical signals (MACD, RSI, Volume)",
                parameters={
                    "type": "object",
                    "properties": {
                        "data": {"type": "object", "description": "Market data"},
                    },
                    "required": ["data"],
                },
                handler=self._analyze_signals_handler,
            )
        )

        self.register_tool(
            PTCToolDefinition(
                name="calculate_position_size",
                description="Calculate optimal position size based on risk",
                parameters={
                    "type": "object",
                    "properties": {
                        "signal_strength": {"type": "number"},
                        "volatility": {"type": "number"},
                        "portfolio_value": {"type": "number"},
                    },
                    "required": ["signal_strength", "volatility", "portfolio_value"],
                },
                handler=self._calculate_position_handler,
            )
        )

        self.register_tool(
            PTCToolDefinition(
                name="execute_trade",
                description="Execute a trade order",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "side": {"type": "string", "enum": ["buy", "sell"]},
                        "quantity": {"type": "number"},
                        "order_type": {
                            "type": "string",
                            "enum": ["market", "limit"],
                        },
                    },
                    "required": ["symbol", "side", "quantity"],
                },
                handler=self._execute_trade_handler,
            )
        )

    def register_tool(self, tool: PTCToolDefinition) -> None:
        """Register a tool for PTC execution."""
        self.tools[tool.name] = tool
        logger.info(f"PTC registered tool: {tool.name}")

    def _build_tool_definitions(self) -> list[dict[str, Any]]:
        """Build Anthropic API tool definitions."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in self.tools.values()
        ]

    def _build_code_execution_tool(self) -> dict[str, Any]:
        """Build the code execution tool definition."""
        return {
            "type": "code_execution",
            "code_execution": {
                "enabled": True,
                # Tools available in code execution environment
                "tools": list(self.tools.keys()),
            },
        }

    def execute_trading_workflow(
        self,
        symbol: str,
        portfolio_value: float = 100000.0,
        context: Optional[dict[str, Any]] = None,
    ) -> PTCExecutionResult:
        """
        Execute a complete trading workflow using PTC.

        Instead of multiple LLM round-trips, Claude writes code that
        orchestrates all tools, with intermediate results staying in sandbox.

        Args:
            symbol: Stock symbol to trade
            portfolio_value: Current portfolio value
            context: Additional context (market regime, etc.)

        Returns:
            PTCExecutionResult with final trading decision
        """
        start_time = datetime.now()

        prompt = f"""You are a trading agent with access to these tools:
{self._format_tools_for_prompt()}

TASK: Analyze {symbol} and determine if we should trade.
Portfolio Value: ${portfolio_value:,.2f}
Context: {json.dumps(context or {})}

Write Python code that:
1. Fetches market data for {symbol}
2. Analyzes technical signals
3. Calculates position size if signal is strong
4. Returns a trading decision

Use the available tools efficiently. Only return the final decision,
keep intermediate calculations in the sandbox.

Important: Return a dict with keys: action, symbol, quantity, confidence, reasoning
"""

        try:
            # Make API call with PTC beta header
            extra_headers = {"anthropic-beta": PTC_BETA_HEADER}

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                extra_headers=extra_headers,
                tools=self._build_tool_definitions()
                + [self._build_code_execution_tool()],
                messages=[{"role": "user", "content": prompt}],
            )

            # Process response
            code_executed = ""
            final_output = None
            tools_invoked = []

            for block in response.content:
                if block.type == "tool_use":
                    tools_invoked.append(block.name)
                    # Execute the tool
                    if block.name in self.tools:
                        result = self.tools[block.name].handler(**block.input)
                        final_output = result
                elif block.type == "text":
                    # Extract any code or reasoning
                    code_executed = block.text
                elif hasattr(block, "type") and block.type == "code_execution_result":
                    # Code execution result from sandbox
                    final_output = getattr(block, "output", None)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return PTCExecutionResult(
                success=True,
                final_output=final_output or self._parse_decision_from_text(code_executed),
                code_executed=code_executed,
                token_usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                execution_time_ms=execution_time,
                tools_invoked=tools_invoked,
            )

        except Exception as e:
            logger.error(f"PTC execution error: {e}")
            return PTCExecutionResult(
                success=False,
                final_output=None,
                code_executed="",
                error=str(e),
            )

    def _format_tools_for_prompt(self) -> str:
        """Format tools for inclusion in prompt."""
        lines = []
        for tool in self.tools.values():
            params = ", ".join(tool.parameters.get("properties", {}).keys())
            lines.append(f"- {tool.name}({params}): {tool.description}")
        return "\n".join(lines)

    def _parse_decision_from_text(self, text: str) -> dict[str, Any]:
        """Parse trading decision from text response."""
        # Default decision if parsing fails
        decision = {
            "action": "HOLD",
            "symbol": "",
            "quantity": 0,
            "confidence": 0.0,
            "reasoning": text[:500] if text else "No reasoning provided",
        }

        # Try to extract structured data
        if "BUY" in text.upper():
            decision["action"] = "BUY"
            decision["confidence"] = 0.6
        elif "SELL" in text.upper():
            decision["action"] = "SELL"
            decision["confidence"] = 0.6

        return decision

    # Tool handlers (implementations)
    def _fetch_market_data_handler(
        self, symbol: str, timeframe: str = "1d"
    ) -> dict[str, Any]:
        """Fetch market data - placeholder for actual implementation."""
        # In production, this would call Alpaca API
        logger.info(f"PTC: Fetching market data for {symbol} ({timeframe})")
        return {
            "symbol": symbol,
            "price": 450.0,  # Placeholder
            "volume": 1000000,
            "volatility": 0.02,
            "timeframe": timeframe,
        }

    def _analyze_signals_handler(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze signals - placeholder for actual implementation."""
        logger.info(f"PTC: Analyzing signals for {data.get('symbol', 'N/A')}")
        return {
            "macd_signal": 0.5,
            "rsi": 55,
            "volume_ratio": 1.2,
            "signal_strength": 0.6,
        }

    def _calculate_position_handler(
        self,
        signal_strength: float,
        volatility: float,
        portfolio_value: float,
    ) -> dict[str, Any]:
        """Calculate position size based on risk."""
        # Simple position sizing: risk 1% per trade
        risk_per_trade = 0.01
        position_value = portfolio_value * risk_per_trade * signal_strength

        logger.info(f"PTC: Position size calculated: ${position_value:.2f}")
        return {
            "position_value": position_value,
            "risk_percent": risk_per_trade * 100,
            "signal_multiplier": signal_strength,
        }

    def _execute_trade_handler(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
    ) -> dict[str, Any]:
        """Execute trade - placeholder for actual implementation."""
        logger.info(f"PTC: Executing {side} {quantity} {symbol} ({order_type})")
        return {
            "order_id": f"ptc_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "status": "submitted",
        }


class PTCMetaAgent:
    """
    Meta-Agent that uses PTC for efficient multi-agent coordination.

    Instead of multiple LLM calls to coordinate agents, uses a single
    PTC execution that orchestrates all analysis in code.
    """

    def __init__(self):
        self.orchestrator = PTCOrchestrator()
        self.name = "PTCMetaAgent"

    def coordinate_analysis(
        self,
        symbol: str,
        market_data: dict[str, Any],
        portfolio_value: float = 100000.0,
    ) -> dict[str, Any]:
        """
        Coordinate all agents using PTC for efficiency.

        Traditional approach: 4+ LLM calls (Research, Signal, Risk, Execution)
        PTC approach: 1 LLM call with code orchestration

        Args:
            symbol: Stock to analyze
            market_data: Current market data
            portfolio_value: Portfolio value for position sizing

        Returns:
            Coordinated trading decision
        """
        context = {
            "market_regime": market_data.get("regime", "UNKNOWN"),
            "volatility": market_data.get("volatility", 0.0),
            "trend_strength": market_data.get("trend_strength", 0.0),
        }

        result = self.orchestrator.execute_trading_workflow(
            symbol=symbol,
            portfolio_value=portfolio_value,
            context=context,
        )

        return {
            "agent": self.name,
            "success": result.success,
            "decision": result.final_output,
            "token_usage": result.token_usage,
            "execution_time_ms": result.execution_time_ms,
            "tools_invoked": result.tools_invoked,
            "ptc_enabled": True,
        }


# Convenience function for quick PTC execution
def execute_ptc_trade(
    symbol: str,
    portfolio_value: float = 100000.0,
) -> PTCExecutionResult:
    """
    Execute a trading workflow using Programmatic Tool Calling.

    Example:
        result = execute_ptc_trade("SPY", portfolio_value=100000)
        if result.success:
            print(f"Decision: {result.final_output}")
            print(f"Tokens used: {result.token_usage}")
    """
    orchestrator = PTCOrchestrator()
    return orchestrator.execute_trading_workflow(
        symbol=symbol,
        portfolio_value=portfolio_value,
    )
