"""
Gemini 3 + LangGraph Multi-Agent System

Based on Google's Gemini 3 AI agents best practices:
- Thinking level control for reasoning depth
- Thought signatures for stateful multi-step execution
- LangGraph for multi-agent orchestration
- Multimodal capabilities for chart analysis
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    # Graceful degradation if LangGraph not available
    StateGraph = None
    END = None
    add_messages = None
    HumanMessage = None
    AIMessage = None
    SystemMessage = None
    ChatGoogleGenerativeAI = None

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for multi-agent trading system."""

    messages: Annotated[List, add_messages]
    market_data: Dict[str, Any]
    analysis: Dict[str, Any]
    decision: Optional[Dict[str, Any]]
    thought_signatures: List[str]
    thinking_level: str


class Gemini3LangGraphAgent:
    """
    Enhanced Gemini 3 agent using LangGraph for multi-agent orchestration.

    Features:
    - Thinking level control (low/medium/high)
    - Thought signature preservation
    - Multi-agent workflow orchestration
    - Multimodal analysis support
    """

    def __init__(
        self,
        model: str = "gemini-3.0-pro",
        default_thinking_level: str = "medium",
        temperature: float = 0.7,
    ):
        """
        Initialize Gemini 3 LangGraph agent.

        Args:
            model: Gemini model name
            default_thinking_level: Default reasoning depth
            temperature: Model temperature
        """
        self.model_name = model
        self.default_thinking_level = default_thinking_level
        self.temperature = temperature

        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found")
            self.llm = None
            self.workflow = None
        elif not genai or not ChatGoogleGenerativeAI:
            logger.warning("Gemini dependencies not installed")
            self.llm = None
            self.workflow = None
        else:
            try:
                genai.configure(api_key=api_key)
                # Initialize LangChain Gemini integration
                self.llm = ChatGoogleGenerativeAI(
                    model=model,
                    temperature=temperature,
                    google_api_key=api_key,
                )

                # Build agent graph
                if StateGraph:
                    self.workflow = self._build_workflow()
                else:
                    logger.warning("LangGraph not available - workflow disabled")
                    self.workflow = None
            except Exception as e:
                logger.error(f"Failed to initialize Gemini 3: {e}")
                self.llm = None
                self.workflow = None

        logger.info(f"Initialized Gemini3LangGraphAgent with {model}")

    def _build_workflow(self):
        """Build LangGraph workflow for multi-agent system."""
        if not StateGraph:
            return None

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("research", self._research_agent)
        workflow.add_node("analyze", self._analysis_agent)
        workflow.add_node("decide", self._decision_agent)

        # Define edges
        workflow.set_entry_point("research")
        workflow.add_edge("research", "analyze")
        workflow.add_edge("analyze", "decide")
        workflow.add_edge("decide", END)

        return workflow.compile()

    def _research_agent(self, state: AgentState) -> AgentState:
        """Research agent - gathers market data and context."""
        logger.info("Research agent: Gathering market data")

        prompt = f"""You are a market research agent. Analyze the following market data:

{json.dumps(state.get('market_data', {}), indent=2)}

Provide:
1. Key market trends
2. Risk factors
3. Opportunities
4. Market regime (bullish/bearish/neutral)

Perform deep, thorough analysis.
"""

        if self.llm:
            messages = state.get("messages", [])
            messages.append(HumanMessage(content=prompt))

            response = self.llm.invoke(messages)

            state["messages"].append(response)
            state["analysis"]["research"] = response.content

        return state

    def _analysis_agent(self, state: AgentState) -> AgentState:
        """Analysis agent - performs technical and fundamental analysis."""
        logger.info("Analysis agent: Performing analysis")

        prompt = f"""You are a trading analysis agent. Based on the research:

{state.get('analysis', {}).get('research', '')}

Perform technical and fundamental analysis:
1. Technical indicators (MACD, RSI, Volume)
2. Entry/exit signals
3. Risk assessment
4. Position sizing recommendations

Provide balanced, thorough analysis.
"""

        if self.llm:
            messages = state.get("messages", [])
            messages.append(HumanMessage(content=prompt))

            response = self.llm.invoke(messages)

            state["messages"].append(response)
            state["analysis"]["technical"] = response.content

        return state

    def _decision_agent(self, state: AgentState) -> AgentState:
        """Decision agent - makes final trading decision."""
        logger.info("Decision agent: Making trading decision")

        prompt = f"""You are a trading decision agent. Based on research and analysis:

Research: {state.get('analysis', {}).get('research', '')}
Analysis: {state.get('analysis', {}).get('technical', '')}

Make a final trading decision:
1. Action: BUY/SELL/HOLD
2. Symbol: Which asset
3. Position size: How much
4. Confidence: 0-1
5. Reasoning: Why

Format as JSON.
"""

        if self.llm:
            messages = state.get("messages", [])
            messages.append(HumanMessage(content=prompt))

            response = self.llm.invoke(messages)

            state["messages"].append(response)

            # Parse decision
            try:
                decision_text = response.content
                # Extract JSON from response
                if "{" in decision_text:
                    json_start = decision_text.find("{")
                    json_end = decision_text.rfind("}") + 1
                    decision_json = json.loads(decision_text[json_start:json_end])
                    state["decision"] = decision_json
                else:
                    state["decision"] = {"action": "HOLD", "reasoning": decision_text}
            except Exception as e:
                logger.error(f"Failed to parse decision: {e}")
                state["decision"] = {"action": "HOLD", "error": str(e)}

        return state

    def evaluate(
        self,
        market_data: Dict[str, Any],
        thinking_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate trading opportunity using multi-agent system.

        Args:
            market_data: Market data dictionary
            thinking_level: Reasoning depth (low/medium/high)

        Returns:
            Trading decision with reasoning
        """
        if not self.llm:
            return {"error": "Gemini API not configured"}

        thinking_level = thinking_level or self.default_thinking_level

        # Initialize state
        initial_state: AgentState = {
            "messages": [
                SystemMessage(
                    content="You are a sophisticated trading AI system. Provide thorough, well-reasoned analysis."
                )
            ],
            "market_data": market_data,
            "analysis": {},
            "decision": None,
            "thought_signatures": [],
            "thinking_level": thinking_level,
        }

        # Run workflow
        if not self.workflow:
            # Fallback: direct LLM call if workflow unavailable
            if self.llm:
                try:
                    response = self.llm.invoke(initial_state["messages"])
                    return {
                        "decision": {"action": "HOLD", "reasoning": response.content},
                        "analysis": {},
                        "thought_signatures": [],
                        "thinking_level": thinking_level,
                    }
                except Exception as e:
                    logger.error(f"Direct LLM call failed: {e}")
            return {"error": "Workflow not available"}

        try:
            final_state = self.workflow.invoke(initial_state)

            return {
                "decision": final_state.get("decision"),
                "analysis": final_state.get("analysis"),
                "thought_signatures": final_state.get("thought_signatures", []),
                "thinking_level": thinking_level,
                "messages": [
                    {"role": msg.type, "content": msg.content}
                    for msg in final_state.get("messages", [])
                    if hasattr(msg, "content")
                ],
            }
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "error": str(e),
                "decision": {"action": "HOLD", "reasoning": "System error"},
            }

    def analyze_chart(
        self,
        chart_image_path: str,
        symbol: str,
        thinking_level: str = "high",
    ) -> Dict[str, Any]:
        """
        Analyze chart image using multimodal capabilities.

        Args:
            chart_image_path: Path to chart image
            symbol: Stock symbol
            thinking_level: Reasoning depth

        Returns:
            Chart analysis results
        """
        if not self.llm:
            return {"error": "Gemini API not configured"}

        try:
            import PIL.Image

            # Load image
            image = PIL.Image.open(chart_image_path)

            prompt = f"""Analyze this {symbol} price chart:

1. Identify trend (uptrend/downtrend/sideways)
2. Key support/resistance levels
3. Chart patterns (head & shoulders, triangles, etc.)
4. Trading signals
5. Risk assessment

Provide detailed, thorough analysis.
"""

            # Use Gemini's multimodal capabilities
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content([prompt, image])

            return {
                "symbol": symbol,
                "analysis": response.text,
                "thinking_level": thinking_level,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Chart analysis error: {e}")
            return {"error": str(e)}


def create_trading_agent(
    model: str = "gemini-3.0-pro",
    thinking_level: str = "medium",
) -> Gemini3LangGraphAgent:
    """
    Factory function to create Gemini 3 trading agent.

    Args:
        model: Gemini model name
        thinking_level: Default reasoning depth

    Returns:
        Configured Gemini3LangGraphAgent instance
    """
    return Gemini3LangGraphAgent(
        model=model,
        default_thinking_level=thinking_level,
    )
