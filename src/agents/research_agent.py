"""
Research Agent: Multi-modal financial analysis

Responsibilities:
- Analyze company fundamentals
- Process news and sentiment
- Evaluate market context
- Provide investment thesis

Inspired by P1GPT multi-modal analysis framework
"""
import logging
from typing import Dict, Any
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research Agent analyzes fundamentals, news, and sentiment.
    
    Multi-modal approach:
    - Fundamental data (P/E, growth, margins)
    - News sentiment
    - Market context
    """
    
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            role="Multi-modal fundamental analysis and sentiment"
        )
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze fundamentals, news, and sentiment.
        
        Args:
            data: Contains symbol, fundamentals, news, market context
            
        Returns:
            Research analysis with investment thesis
        """
        symbol = data.get("symbol", "UNKNOWN")
        fundamentals = data.get("fundamentals", {})
        news = data.get("news", [])
        market_context = data.get("market_context", {})
        
        # Build comprehensive research prompt
        memory_context = self.get_memory_context(limit=3)
        
        prompt = f"""You are a Research Agent analyzing {symbol} for trading decision.

FUNDAMENTAL DATA:
- P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}
- Growth Rate: {fundamentals.get('growth_rate', 'N/A')}
- Profit Margin: {fundamentals.get('profit_margin', 'N/A')}
- Market Cap: {fundamentals.get('market_cap', 'N/A')}

NEWS & SENTIMENT:
{self._format_news(news)}

MARKET CONTEXT:
- Sector: {market_context.get('sector', 'N/A')}
- Market Trend: {market_context.get('market_trend', 'N/A')}
- Volatility: {market_context.get('volatility', 'N/A')}

{memory_context}

TASK: Provide a comprehensive analysis:
1. Fundamental strength (1-10)
2. Sentiment score (-1 to +1)
3. Investment thesis (2-3 sentences)
4. Recommendation: BUY / SELL / HOLD
5. Confidence (0-1)
6. Key risks

Format your response as:
STRENGTH: [1-10]
SENTIMENT: [-1 to +1]
THESIS: [your thesis]
RECOMMENDATION: [BUY/SELL/HOLD]
CONFIDENCE: [0-1]
RISKS: [key risks]"""

        # Get LLM analysis
        response = self.reason_with_llm(prompt)
        
        # Parse response
        analysis = self._parse_research_response(response["reasoning"])
        analysis["full_reasoning"] = response["reasoning"]
        
        # Log decision
        self.log_decision(analysis)
        
        return analysis
    
    def _format_news(self, news: list) -> str:
        """Format news items for prompt."""
        if not news:
            return "No recent news available."
        
        formatted = ""
        for i, item in enumerate(news[:5], 1):  # Top 5 news items
            formatted += f"{i}. {item.get('title', 'N/A')} ({item.get('date', 'N/A')})\n"
            formatted += f"   Sentiment: {item.get('sentiment', 'neutral')}\n"
        
        return formatted
    
    def _parse_research_response(self, reasoning: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured analysis.
        
        Args:
            reasoning: LLM response text
            
        Returns:
            Structured analysis dict
        """
        lines = reasoning.split("\n")
        analysis = {
            "strength": 5,  # Default values
            "sentiment": 0.0,
            "thesis": "",
            "action": "HOLD",
            "confidence": 0.5,
            "risks": ""
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith("STRENGTH:"):
                try:
                    analysis["strength"] = int(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("SENTIMENT:"):
                try:
                    analysis["sentiment"] = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("THESIS:"):
                analysis["thesis"] = line.split(":", 1)[1].strip()
            elif line.startswith("RECOMMENDATION:"):
                rec = line.split(":")[1].strip().upper()
                if rec in ["BUY", "SELL", "HOLD"]:
                    analysis["action"] = rec
            elif line.startswith("CONFIDENCE:"):
                try:
                    analysis["confidence"] = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("RISKS:"):
                analysis["risks"] = line.split(":", 1)[1].strip()
        
        return analysis

