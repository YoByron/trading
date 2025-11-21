"""
Gemini 3 Agent - Enhanced AI agent using Google Gemini 3 API

This agent leverages Gemini 3's advanced features:
- Adjustable thinking_level for reasoning depth control
- Thought signatures for stateful multi-step execution
- Multimodal capabilities with adjustable fidelity
- Large context window with consistent reasoning
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from src.utils.self_healing import with_retry, health_check

logger = logging.getLogger(__name__)


class GeminiAgent:
    """
    Gemini 3-powered agent for trading decisions.
    
    Features:
    - Dynamic thinking_level adjustment (high for planning, low for speed)
    - Thought signature preservation across tool calls
    - Multimodal analysis support
    - Self-healing retry mechanisms
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        model: str = "gemini-3-pro-preview",
        default_thinking_level: str = "medium"
    ):
        """
        Initialize Gemini 3 agent.
        
        Args:
            name: Agent name
            role: Agent role/responsibility
            model: Gemini model to use
            default_thinking_level: Default reasoning depth (low/medium/high)
        """
        self.name = name
        self.role = role
        self.model = model
        self.default_thinking_level = default_thinking_level
        
        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found, Gemini agent will not function")
        else:
            genai.configure(api_key=api_key)
        
        # Initialize model
        self.client = genai.GenerativeModel(model)
        
        # Memory and decision tracking
        self.memory: List[Dict[str, Any]] = []
        self.decision_log: List[Dict[str, Any]] = []
        self.thought_signatures: List[str] = []
        
        logger.info(f"Initialized {name} with Gemini 3 ({model})")
    
    @with_retry(max_attempts=3, backoff=2.0)
    def reason(
        self,
        prompt: str,
        thinking_level: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Use Gemini 3 reasoning to make decisions.
        
        Args:
            prompt: The reasoning prompt
            thinking_level: Reasoning depth (low/medium/high), defaults to agent's default
            tools: Optional tool definitions for function calling
            context: Optional conversation context with thought signatures
            
        Returns:
            Response with reasoning, decision, and thought signature
        """
        thinking_level = thinking_level or self.default_thinking_level
        
        try:
            # Build generation config
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,
            }
            
            # Add thinking level if supported
            if hasattr(genai.types, "ThinkingLevel"):
                generation_config["thinking_level"] = thinking_level
            
            # Build conversation history with thought signatures
            messages = []
            if context:
                messages.extend(context)
            
            # Add current prompt
            messages.append({"role": "user", "parts": [prompt]})
            
            # Generate response
            if tools:
                response = self.client.generate_content(
                    messages,
                    generation_config=generation_config,
                    tools=tools
                )
            else:
                response = self.client.generate_content(
                    messages,
                    generation_config=generation_config
                )
            
            # Extract thought signature if available
            thought_signature = None
            if hasattr(response, "thought_signature"):
                thought_signature = response.thought_signature
                self.thought_signatures.append(thought_signature)
            
            # Parse response
            result = {
                "reasoning": response.text if hasattr(response, "text") else "",
                "decision": "",
                "confidence": 0.0,
                "thought_signature": thought_signature,
                "tool_calls": [],
                "thinking_level": thinking_level
            }
            
            # Extract function calls if present
            if hasattr(response, "function_calls"):
                for call in response.function_calls:
                    result["tool_calls"].append({
                        "name": call.name,
                        "args": dict(call.args)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name} Gemini reasoning error: {e}")
            return {
                "reasoning": f"Error: {str(e)}",
                "decision": "NO_ACTION",
                "confidence": 0.0,
                "thought_signature": None,
                "tool_calls": [],
                "thinking_level": thinking_level
            }
    
    def analyze_with_context(
        self,
        data: Dict[str, Any],
        thinking_level: str = "high"
    ) -> Dict[str, Any]:
        """
        Analyze data with full context preservation.
        
        Args:
            data: Input data for analysis
            thinking_level: Reasoning depth for this analysis
            
        Returns:
            Analysis results with preserved thought signatures
        """
        # Build context from previous thought signatures
        context = []
        for i, sig in enumerate(self.thought_signatures[-5:]):  # Last 5 signatures
            context.append({
                "role": "model",
                "parts": [f"[Thought Signature {i}]"],
                "thought_signature": sig
            })
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(data)
        
        # Reason with context
        result = self.reason(
            prompt=prompt,
            thinking_level=thinking_level,
            context=context
        )
        
        # Log decision
        self.log_decision(result)
        
        return result
    
    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Build analysis prompt from data."""
        return f"""You are {self.name}, responsible for: {self.role}

Analyze the following data and provide your recommendation:

{json.dumps(data, indent=2)}

Provide:
1. Your reasoning
2. Recommended action
3. Confidence level (0-1)
4. Key factors influencing your decision
"""
    
    def log_decision(self, decision: Dict[str, Any]) -> None:
        """Log a decision for audit trail."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "decision": decision,
            "thought_signature": decision.get("thought_signature")
        }
        self.decision_log.append(entry)
        logger.info(f"{self.name} decision logged")
    
    def get_memory_context(self, limit: int = 10) -> str:
        """Get recent memory context for reasoning."""
        recent_memories = self.memory[-limit:]
        if not recent_memories:
            return "No previous experience."
        
        context = "Recent experience:\n"
        for mem in recent_memories:
            outcome = mem.get("outcome", {})
            context += f"- {mem['timestamp']}: {outcome.get('result', 'N/A')}\n"
        
        return context
    
    def health_check(self) -> bool:
        """Run health check on agent."""
        return health_check(threshold=5, window_seconds=3600)
