"""
Gemini 3 Integration - Enhanced Trading Agent

Integrates Gemini 3 with trading system using Google's best practices:
- Thinking level control
- Thought signatures
- LangGraph orchestration
"""

import os
import logging
from typing import Dict, Any, Optional

from src.agents.gemini3_langgraph_agent import create_trading_agent, Gemini3LangGraphAgent

logger = logging.getLogger(__name__)


class Gemini3TradingIntegration:
    """
    Integration layer for Gemini 3 in trading system.
    
    Provides:
    - Market analysis with adjustable thinking depth
    - Multi-agent orchestration via LangGraph
    - Chart analysis with multimodal capabilities
    - Stateful reasoning with thought signatures
    """
    
    def __init__(self):
        """Initialize Gemini 3 integration."""
        self.agent: Optional[Gemini3LangGraphAgent] = None
        self.enabled = False
        
        # Check if Gemini API key is available
        if os.getenv("GOOGLE_API_KEY"):
            try:
                self.agent = create_trading_agent(
                    model="gemini-3.0-pro",
                    thinking_level="medium",
                )
                self.enabled = True
                logger.info("Gemini 3 integration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini 3: {e}")
        else:
            logger.info("GOOGLE_API_KEY not set - Gemini 3 integration disabled")
    
    def analyze_market(
        self,
        symbols: list[str],
        market_data: Dict[str, Any],
        thinking_level: str = "medium",
    ) -> Dict[str, Any]:
        """
        Analyze market using Gemini 3 multi-agent system.
        
        Args:
            symbols: List of symbols to analyze
            market_data: Market data dictionary
            thinking_level: Reasoning depth (low/medium/high)
            
        Returns:
            Analysis results with trading recommendations
        """
        if not self.enabled or not self.agent:
            return {"error": "Gemini 3 not available"}
        
        try:
            # Prepare market data
            analysis_data = {
                "symbols": symbols,
                "market_data": market_data,
                "timestamp": market_data.get("timestamp"),
            }
            
            # Evaluate using multi-agent system
            result = self.agent.evaluate(
                market_data=analysis_data,
                thinking_level=thinking_level,
            )
            
            return result
        except Exception as e:
            logger.error(f"Gemini 3 analysis error: {e}")
            return {"error": str(e)}
    
    def analyze_chart(
        self,
        chart_path: str,
        symbol: str,
        thinking_level: str = "high",
    ) -> Dict[str, Any]:
        """
        Analyze price chart using multimodal capabilities.
        
        Args:
            chart_path: Path to chart image
            symbol: Stock symbol
            thinking_level: Reasoning depth
            
        Returns:
            Chart analysis results
        """
        if not self.enabled or not self.agent:
            return {"error": "Gemini 3 not available"}
        
        return self.agent.analyze_chart(
            chart_image_path=chart_path,
            symbol=symbol,
            thinking_level=thinking_level,
        )
    
    def get_trading_recommendation(
        self,
        symbol: str,
        market_context: Dict[str, Any],
        thinking_level: str = "high",
    ) -> Dict[str, Any]:
        """
        Get trading recommendation for a symbol.
        
        Args:
            symbol: Stock symbol
            market_context: Market context data
            thinking_level: Reasoning depth
            
        Returns:
            Trading recommendation with reasoning
        """
        if not self.enabled or not self.agent:
            return {"error": "Gemini 3 not available"}
        
        market_data = {
            "symbol": symbol,
            **market_context,
        }
        
        result = self.analyze_market(
            symbols=[symbol],
            market_data=market_data,
            thinking_level=thinking_level,
        )
        
        return result


# Global instance
_gemini3_integration: Optional[Gemini3TradingIntegration] = None


def get_gemini3_integration() -> Gemini3TradingIntegration:
    """Get or create Gemini 3 integration instance."""
    global _gemini3_integration
    if _gemini3_integration is None:
        _gemini3_integration = Gemini3TradingIntegration()
    return _gemini3_integration

