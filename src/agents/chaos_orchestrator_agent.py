import logging
import random
from typing import Dict, Any
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.safety.chaos_monkey import chaos_monkey
from src.orchestration.elite_orchestrator import EliteOrchestrator

logger = logging.getLogger(__name__)

class ChaosOrchestratorAgent(BaseAgent):
    """
    Chaos Orchestrator Agent: Autonomous Resilience Testing.
    
    Responsibilities:
    - Schedule and execute Chaos Drills
    - Determine drill parameters (latency, error rates) based on system stability
    - Analyze drill results and adjust future tests
    """
    
    def __init__(self):
        super().__init__(
            name="ChaosOrchestratorAgent",
            role="Resilience testing and chaos engineering orchestration"
        )
        
    def analyze(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Decide whether to run a chaos drill.
        
        Args:
            data: System health data (optional)
            
        Returns:
            Drill decision and results
        """
        logger.info("🔥 Chaos Orchestrator: Evaluating drill conditions...")
        
        # 1. Decide on Drill Parameters using LLM
        # In a real system, this would look at recent stability. 
        # For now, we randomize slightly but ask LLM for "approval" to simulate reasoning.
        
        prompt = """You are the Chaos Orchestrator. 
        Current System Status: STABLE (Assumed).
        Last Drill: Unknown.
        
        Decide:
        1. Should we run a chaos drill now? (YES/NO)
        2. If YES, what intensity? (LOW/MEDIUM/HIGH)
           - LOW: 10% failure rate, 100-500ms latency
           - MEDIUM: 30% failure rate, 500-2000ms latency
           - HIGH: 50% failure rate, 1000-5000ms latency
           
        Provide reasoning based on "maintaining anti-fragility".
        """
        
        response = self.reason_with_llm(prompt)
        reasoning = response.get("reasoning", "").upper()
        
        if "NO" in reasoning and "YES" not in reasoning:
             return {
                "action": "SKIP_DRILL",
                "reasoning": reasoning
            }
            
        # Parse intensity
        intensity = "LOW"
        if "HIGH" in reasoning: intensity = "HIGH"
        elif "MEDIUM" in reasoning: intensity = "MEDIUM"
        
        # 2. Configure Chaos Monkey
        config = self._get_config_for_intensity(intensity)
        chaos_monkey.enabled = True
        chaos_monkey.probability = config["probability"]
        
        self.log_decision({
            "action": "START_DRILL",
            "intensity": intensity,
            "config": config
        })
        
        # 3. Execute Drill (Run a trading cycle under chaos)
        logger.info(f"🚀 STARTING {intensity} INTENSITY CHAOS DRILL")
        orchestrator = EliteOrchestrator(paper=True)
        
        drill_results = {}
        try:
            # We inject latency/errors into this specific run via the global chaos_monkey we just configured
            drill_results = orchestrator.run_trading_cycle(symbols=["SPY", "QQQ"])
            drill_results["status"] = "SURVIVED"
        except Exception as e:
            logger.error(f"❌ System FAILED Chaos Drill: {e}")
            drill_results["status"] = "FAILED"
            drill_results["error"] = str(e)
        finally:
            # Reset Chaos Monkey
            chaos_monkey.enabled = False
            
        # 4. Report
        return {
            "action": "DRILL_COMPLETE",
            "intensity": intensity,
            "result": drill_results["status"],
            "details": drill_results
        }

    def _get_config_for_intensity(self, intensity: str) -> Dict[str, Any]:
        if intensity == "HIGH":
            return {"probability": 0.5, "min_ms": 1000, "max_ms": 5000}
        elif intensity == "MEDIUM":
            return {"probability": 0.3, "min_ms": 500, "max_ms": 2000}
        else:
            return {"probability": 0.1, "min_ms": 100, "max_ms": 500}
