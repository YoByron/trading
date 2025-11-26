"""
Base Agent Class - Foundation for all trading agents
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from src.utils.self_healing import with_retry, health_check

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all trading agents.
    
    Each agent has:
    - LLM reasoning capability (Claude)
    - Tool orchestration (can call external APIs)
    - Memory (learns from past decisions)
    - Transparency (auditable decision logs)
    """
    
    def __init__(self, name: str, role: str, model: str = "claude-3-opus-20240229"):
        self.name = name
        self.role = role
        self.model = model
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.memory: List[Dict[str, Any]] = []
        self.decision_log: List[Dict[str, Any]] = []
        
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis method - must be implemented by each agent.
        
        Args:
            data: Input data for analysis
            
        Returns:
            Analysis results with reasoning
        """
        pass
    
    @with_retry(max_attempts=3, backoff=2.0)
    def reason_with_llm(self, prompt: str, tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Use LLM reasoning to make decisions.
        
        Args:
            prompt: The reasoning prompt
            tools: Optional tool definitions for tool use
            
        Returns:
            LLM response with reasoning
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            
            if tools:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=messages,
                    tools=tools
                )
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=messages
                )
            
            # Extract text content
            result = {
                "reasoning": "",
                "decision": "",
                "confidence": 0.0,
                "tool_calls": []
            }
            
            for block in response.content:
                if block.type == "text":
                    result["reasoning"] = block.text
                elif block.type == "tool_use":
                    result["tool_calls"].append({
                        "name": block.name,
                        "input": block.input
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name} LLM reasoning error: {e}")
            return {
                "reasoning": f"Error: {str(e)}",
                "decision": "NO_ACTION",
                "confidence": 0.0,
                "tool_calls": []
            }
    
    def log_decision(self, decision: Dict[str, Any]) -> None:
        """Log a decision for audit trail and learning."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "decision": decision
        }
        self.decision_log.append(entry)
        logger.info(f"{self.name} decision logged: {decision.get('action', 'N/A')}")
    
    def learn_from_outcome(self, decision_id: str, outcome: Dict[str, Any]) -> None:
        """
        Learn from decision outcomes (reinforcement learning).
        
        Args:
            decision_id: ID of the decision
            outcome: Result data (profit/loss, accuracy, etc.)
        """
        memory_entry = {
            "decision_id": decision_id,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        }
        self.memory.append(memory_entry)
        logger.info(f"{self.name} learned from outcome: {outcome.get('result', 'N/A')}")
    
    def get_memory_context(self, limit: int = 10) -> str:
        """
        Get recent memory context for LLM reasoning.
        
        Args:
            limit: Number of recent memories to include
            
        Returns:
            Formatted memory context string
        """
        recent_memories = self.memory[-limit:]
        if not recent_memories:
            return "No previous experience."
        
        context = "Recent experience:\n"
        for mem in recent_memories:
            outcome = mem.get("outcome", {})
            context += f"- {mem['timestamp']}: {outcome.get('result', 'N/A')} "
            context += f"(P/L: {outcome.get('pl', 0):.2f})\n"
        
        return context

