"""
Elite AI Trading Orchestrator
World-class multi-agent system combining:
- Claude Agents SDK + Skills (core flows)
- Langchain Agents (RAG, multi-modal fusion)
- Gemini Agents (research, long-horizon planning)
- Go ADK Agents (high-speed execution)
- Planning-first agentic flows
- Context engineering with persistent storage
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio

from src.core.skills_integration import get_skills

logger = logging.getLogger(__name__)


class PlanningPhase(Enum):
    """Planning phases for agentic flows"""
    INITIALIZE = "initialize"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    RISK_ASSESSMENT = "risk_assessment"
    EXECUTION = "execution"
    AUDIT = "audit"


class AgentType(Enum):
    """Agent types in the system"""
    CLAUDE_SKILLS = "claude_skills"
    LANGCHAIN = "langchain"
    GEMINI = "gemini"
    GO_ADK = "go_adk"
    MCP = "mcp"
    ML_MODEL = "ml_model"


@dataclass
class TradePlan:
    """Planning-first trade plan"""
    plan_id: str
    timestamp: str
    symbols: List[str]
    phases: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "planning"
    git_commit: Optional[str] = None


@dataclass
class AgentResult:
    """Result from an agent execution"""
    agent_type: AgentType
    success: bool
    data: Dict[str, Any]
    confidence: float = 0.0
    reasoning: str = ""
    errors: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0


class EliteOrchestrator:
    """
    Elite AI Trading Orchestrator
    
    Combines all agent frameworks into a unified, planning-first system:
    1. Planning phase: Explicit planning before acting
    2. Multi-agent coordination: Claude Skills, Langchain, Gemini, Go ADK
    3. Context engineering: Persistent storage outside prompts
    4. Hybrid orchestration: Each agent type for its strengths
    5. Autonomous operation: Minimal human intervention
    """
    
    def __init__(self, paper: bool = True, enable_planning: bool = True):
        """
        Initialize Elite Orchestrator
        
        Args:
            paper: Paper trading mode
            enable_planning: Enable planning-first flows
        """
        self.paper = paper
        self.enable_planning = enable_planning
        
        # Initialize all agent frameworks
        self.skills = get_skills()
        self.mcp_orchestrator = None
        self.adk_adapter = None
        self.langchain_agent = None
        self.gemini_agent = None
        
        # Planning storage
        self.plans_dir = Path("data/trading_plans")
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        
        # Context storage
        self.context_dir = Path("data/agent_context")
        self.context_dir.mkdir(parents=True, exist_ok=True)
        
        # Audit trail
        self.audit_dir = Path("data/audit_trail")
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialize_agents()
        
        logger.info("✅ Elite Orchestrator initialized")
        logger.info(f"   Planning: {'Enabled' if enable_planning else 'Disabled'}")
        logger.info(f"   Mode: {'PAPER' if paper else 'LIVE'}")
    
    def _initialize_agents(self):
        """Initialize all agent frameworks"""
        # MCP Orchestrator (multi-agent system) - Lazy import
        try:
            from src.orchestration.mcp_trading import MCPTradingOrchestrator
            self.mcp_orchestrator = MCPTradingOrchestrator(
                symbols=["SPY", "QQQ", "VOO"],
                paper=self.paper
            )
            logger.info("✅ MCP Orchestrator initialized")
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"⚠️ MCP Orchestrator unavailable (dependencies missing): {e}")
            self.mcp_orchestrator = None
        except Exception as e:
            logger.warning(f"⚠️ MCP Orchestrator unavailable: {e}")
            self.mcp_orchestrator = None
        
        # Go ADK Adapter (high-speed execution) - Lazy import
        try:
            from src.orchestration.adk_integration import ADKTradeAdapter
            self.adk_adapter = ADKTradeAdapter(paper=self.paper)
            if self.adk_adapter.enabled:
                logger.info("✅ Go ADK Adapter initialized")
            else:
                logger.info("⚠️ Go ADK Adapter disabled")
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"⚠️ Go ADK Adapter unavailable (dependencies missing): {e}")
            self.adk_adapter = None
        except Exception as e:
            logger.warning(f"⚠️ Go ADK Adapter unavailable: {e}")
            self.adk_adapter = None
        
        # Langchain Agent (RAG, multi-modal fusion)
        try:
            from langchain_agents.agents import build_price_action_agent
            self.langchain_agent = build_price_action_agent()
            logger.info("✅ Langchain Agent initialized")
        except Exception as e:
            logger.warning(f"⚠️ Langchain Agent unavailable: {e}")
        
        # Gemini Agent (research, long-horizon planning)
        try:
            from src.agents.gemini_agent import GeminiAgent
            self.gemini_agent = GeminiAgent(
                name="EliteGemini",
                model="gemini-3-pro-preview"
            )
            logger.info("✅ Gemini Agent initialized")
        except Exception as e:
            logger.warning(f"⚠️ Gemini Agent unavailable: {e}")
            
        # ML Predictor (LSTM-PPO)
        try:
            from src.ml.inference import MLPredictor
            self.ml_predictor = MLPredictor()
            logger.info("✅ ML Predictor (LSTM-PPO) initialized")
        except Exception as e:
            logger.warning(f"⚠️ ML Predictor unavailable: {e}")
            self.ml_predictor = None
    
    def create_trade_plan(self, symbols: List[str], context: Optional[Dict[str, Any]] = None) -> TradePlan:
        """
        Create a planning-first trade plan
        
        Args:
            symbols: Symbols to trade
            context: Additional context
            
        Returns:
            TradePlan with explicit planning phases
        """
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        plan = TradePlan(
            plan_id=plan_id,
            timestamp=datetime.now().isoformat(),
            symbols=symbols,
            context=context or {}
        )
        
        # Define planning phases
        plan.phases = {
            PlanningPhase.INITIALIZE.value: {
                "description": "Initialize trading cycle",
                "agents": [AgentType.CLAUDE_SKILLS.value],
                "tasks": [
                    "Load portfolio state",
                    "Check market hours",
                    "Validate account status"
                ],
                "status": "pending"
            },
            PlanningPhase.DATA_COLLECTION.value: {
                "description": "Collect market data and signals",
                "agents": [
                    AgentType.CLAUDE_SKILLS.value,
                    AgentType.LANGCHAIN.value,
                    AgentType.GEMINI.value
                ],
                "tasks": [
                    "Fetch price data",
                    "Retrieve news sentiment",
                    "Gather social signals",
                    "Load alternative data"
                ],
                "status": "pending"
            },
            PlanningPhase.ANALYSIS.value: {
                "description": "Multi-agent analysis",
                "agents": [
                    AgentType.LANGCHAIN.value,
                    AgentType.GEMINI.value,
                    AgentType.MCP.value,
                    AgentType.ML_MODEL.value
                ],
                "tasks": [
                    "Technical analysis",
                    "Fundamental analysis",
                    "Sentiment analysis",
                    "Ensemble voting"
                ],
                "status": "pending"
            },
            PlanningPhase.RISK_ASSESSMENT.value: {
                "description": "Risk validation",
                "agents": [AgentType.CLAUDE_SKILLS.value],
                "tasks": [
                    "Portfolio health check",
                    "Position sizing",
                    "Stop-loss calculation",
                    "Circuit breaker check"
                ],
                "status": "pending"
            },
            PlanningPhase.EXECUTION.value: {
                "description": "Trade execution",
                "agents": [
                    AgentType.GO_ADK.value,
                    AgentType.MCP.value
                ],
                "tasks": [
                    "Order placement",
                    "Execution monitoring",
                    "Anomaly detection"
                ],
                "status": "pending"
            },
            PlanningPhase.AUDIT.value: {
                "description": "Post-trade audit",
                "agents": [AgentType.CLAUDE_SKILLS.value],
                "tasks": [
                    "Performance tracking",
                    "Trade logging",
                    "Git commit"
                ],
                "status": "pending"
            }
        }
        
        # Save plan to persistent storage
        self._save_plan(plan)
        
        logger.info(f"📋 Created trade plan: {plan_id} for {len(symbols)} symbols")
        return plan
    
    def execute_plan(self, plan: TradePlan) -> Dict[str, Any]:
        """
        Execute a trade plan with multi-agent coordination
        
        Args:
            plan: Trade plan to execute
            
        Returns:
            Execution results
        """
        logger.info(f"🚀 Executing plan: {plan.plan_id}")
        
        results = {
            "plan_id": plan.plan_id,
            "phases": {},
            "agent_results": [],
            "final_decision": None,
            "errors": []
        }
        
        # Phase 1: Initialize
        try:
            init_result = self._execute_phase(plan, PlanningPhase.INITIALIZE)
            results["phases"][PlanningPhase.INITIALIZE.value] = init_result
            plan.phases[PlanningPhase.INITIALIZE.value]["status"] = "completed"
        except Exception as e:
            logger.error(f"Phase 1 failed: {e}")
            results["errors"].append(f"Initialize: {str(e)}")
            return results
        
        # Phase 2: Data Collection (multi-agent)
        try:
            data_result = self._execute_data_collection(plan)
            results["phases"][PlanningPhase.DATA_COLLECTION.value] = data_result
            plan.phases[PlanningPhase.DATA_COLLECTION.value]["status"] = "completed"
        except Exception as e:
            logger.error(f"Phase 2 failed: {e}")
            results["errors"].append(f"Data Collection: {str(e)}")
        
        # Phase 3: Analysis (ensemble voting)
        try:
            analysis_result = self._execute_analysis(plan)
            results["phases"][PlanningPhase.ANALYSIS.value] = analysis_result
            plan.phases[PlanningPhase.ANALYSIS.value]["status"] = "completed"
            results["agent_results"].extend(analysis_result.get("agent_results", []))
        except Exception as e:
            logger.error(f"Phase 3 failed: {e}")
            results["errors"].append(f"Analysis: {str(e)}")
        
        # Phase 4: Risk Assessment
        try:
            risk_result = self._execute_risk_assessment(plan)
            results["phases"][PlanningPhase.RISK_ASSESSMENT.value] = risk_result
            plan.phases[PlanningPhase.RISK_ASSESSMENT.value]["status"] = "completed"
            
            # Check if trading should halt
            if risk_result.get("should_halt"):
                logger.warning("🚫 Trading halted by risk assessment")
                plan.status = "halted"
                self._save_plan(plan)
                return results
        except Exception as e:
            logger.error(f"Phase 4 failed: {e}")
            results["errors"].append(f"Risk Assessment: {str(e)}")
        
        # Phase 5: Execution
        try:
            exec_result = self._execute_trades(plan, analysis_result)
            results["phases"][PlanningPhase.EXECUTION.value] = exec_result
            plan.phases[PlanningPhase.EXECUTION.value]["status"] = "completed"
            results["final_decision"] = exec_result.get("decision")
        except Exception as e:
            logger.error(f"Phase 5 failed: {e}")
            results["errors"].append(f"Execution: {str(e)}")
        
        # Phase 6: Audit
        try:
            audit_result = self._execute_audit(plan, results)
            results["phases"][PlanningPhase.AUDIT.value] = audit_result
            plan.phases[PlanningPhase.AUDIT.value]["status"] = "completed"
        except Exception as e:
            logger.error(f"Phase 6 failed: {e}")
            results["errors"].append(f"Audit: {str(e)}")
        
        plan.status = "completed"
        self._save_plan(plan)
        self._save_results(plan.plan_id, results)
        
        logger.info(f"✅ Plan execution complete: {plan.plan_id}")
        return results
    
    def _execute_phase(self, plan: TradePlan, phase: PlanningPhase) -> Dict[str, Any]:
        """Execute a single phase"""
        phase_config = plan.phases[phase.value]
        results = {
            "phase": phase.value,
            "tasks": {},
            "agent_results": []
        }
        
        for task in phase_config["tasks"]:
            # Use Claude Skills for initialization
            if phase == PlanningPhase.INITIALIZE:
                if task == "Load portfolio state":
                    health_result = self.skills.assess_portfolio_health()
                    results["tasks"][task] = health_result
                elif task == "Check market hours":
                    # Use Financial Data Fetcher skill
                    if self.skills.financial_data_fetcher:
                        market_result = self.skills.get_price_data(
                            symbols=plan.symbols[:1],  # Check one symbol
                            timeframe="1Min",
                            limit=1
                        )
                        results["tasks"][task] = market_result
        
        return results
    
    def _execute_data_collection(self, plan: TradePlan) -> Dict[str, Any]:
        """Execute data collection phase with multiple agents"""
        results = {
            "phase": PlanningPhase.DATA_COLLECTION.value,
            "data_sources": {},
            "agent_results": []
        }
        
        # Claude Skills: Financial Data
        if self.skills.financial_data_fetcher:
            for symbol in plan.symbols:
                data_result = self.skills.get_price_data(
                    symbols=[symbol],
                    timeframe="1Day",
                    limit=30
                )
                results["data_sources"][f"{symbol}_price"] = data_result
        
        # Langchain: RAG for news/sentiment
        if self.langchain_agent:
            for symbol in plan.symbols:
                try:
                    prompt = f"Analyze recent news and sentiment for {symbol}. Provide key insights."
                    langchain_result = self.langchain_agent.invoke({"input": prompt})
                    results["data_sources"][f"{symbol}_sentiment"] = {
                        "agent": "langchain",
                        "data": str(langchain_result)
                    }
                except Exception as e:
                    logger.warning(f"Langchain data collection failed for {symbol}: {e}")
        
        # Gemini: Long-horizon research
        if self.gemini_agent:
            for symbol in plan.symbols:
                try:
                    research_prompt = f"Provide long-term research analysis for {symbol}. Consider fundamentals, trends, and portfolio fit."
                    gemini_result = self.gemini_agent.reason(prompt=research_prompt)
                    results["data_sources"][f"{symbol}_research"] = {
                        "agent": "gemini",
                        "data": gemini_result
                    }
                except Exception as e:
                    logger.warning(f"Gemini research failed for {symbol}: {e}")
        
        return results
    
    def _execute_analysis(self, plan: TradePlan) -> Dict[str, Any]:
        """Execute analysis phase with ensemble voting"""
        results = {
            "phase": PlanningPhase.ANALYSIS.value,
            "agent_results": [],
            "ensemble_vote": {}
        }
        
        # Collect recommendations from all agents
        recommendations = {}
        
        # MCP Orchestrator (multi-agent system)
        if self.mcp_orchestrator:
            try:
                mcp_result = self.mcp_orchestrator.run_once(execute_orders=False)
                for symbol in plan.symbols:
                    if symbol in mcp_result.get("symbols", []):
                        recommendations[f"{symbol}_mcp"] = {
                            "agent": "mcp",
                            "recommendation": mcp_result.get("symbols", {}).get(symbol, {}),
                            "confidence": 0.8
                        }
            except Exception as e:
                logger.warning(f"MCP analysis failed: {e}")
        
        # Langchain Agent
        if self.langchain_agent:
            for symbol in plan.symbols:
                try:
                    prompt = f"Should we trade {symbol}? Provide recommendation with reasoning."
                    langchain_result = self.langchain_agent.invoke({"input": prompt})
                    text = str(langchain_result)
                    approve = "approve" in text.lower() and "decline" not in text.lower()
                    recommendations[f"{symbol}_langchain"] = {
                        "agent": "langchain",
                        "recommendation": "BUY" if approve else "HOLD",
                        "confidence": 0.7,
                        "reasoning": text[:200]
                    }
                except Exception as e:
                    logger.warning(f"Langchain analysis failed for {symbol}: {e}")
        
        # Gemini Agent
        if self.gemini_agent:
            for symbol in plan.symbols:
                try:
                    gemini_prompt = f"Analyze {symbol} for trading. Consider long-term portfolio fit and risk."
                    gemini_result = self.gemini_agent.reason(prompt=gemini_prompt)
                    decision = gemini_result.get("decision", "").upper()
                    recommendations[f"{symbol}_gemini"] = {
                        "agent": "gemini",
                        "recommendation": decision if decision else "HOLD",
                        "confidence": 0.75,
                        "reasoning": gemini_result.get("reasoning", "")[:200]
                    }
                except Exception as e:
                    logger.warning(f"Gemini analysis failed for {symbol}: {e}")

        # ML Predictor (LSTM-PPO)
        if self.ml_predictor:
            for symbol in plan.symbols:
                try:
                    ml_signal = self.ml_predictor.get_signal(symbol)
                    recommendations[f"{symbol}_ml"] = {
                        "agent": "ml_model",
                        "recommendation": ml_signal["action"],
                        "confidence": ml_signal["confidence"],
                        "reasoning": f"LSTM-PPO Value Estimate: {ml_signal.get('value_estimate', 0):.2f}"
                    }
                except Exception as e:
                    logger.warning(f"ML prediction failed for {symbol}: {e}")
        
        # Ensemble voting
        for symbol in plan.symbols:
            symbol_recs = {k: v for k, v in recommendations.items() if symbol in k}
            if symbol_recs:
                buy_votes = sum(1 for r in symbol_recs.values() if r.get("recommendation") == "BUY")
                total_votes = len(symbol_recs)
                results["ensemble_vote"][symbol] = {
                    "buy_votes": buy_votes,
                    "total_votes": total_votes,
                    "consensus": "BUY" if buy_votes >= total_votes * 0.6 else "HOLD",
                    "recommendations": symbol_recs
                }
        
        results["agent_results"] = list(recommendations.values())
        return results
    
    def _execute_risk_assessment(self, plan: TradePlan) -> Dict[str, Any]:
        """Execute risk assessment phase"""
        results = {
            "phase": PlanningPhase.RISK_ASSESSMENT.value,
            "should_halt": False,
            "risk_checks": {}
        }
        
        # Portfolio health check
        health_result = self.skills.assess_portfolio_health()
        results["risk_checks"]["portfolio_health"] = health_result
        
        if health_result.get("success"):
            health_data = health_result.get("data", {})
            if health_data.get("overall_status") == "HALTED":
                results["should_halt"] = True
                logger.warning("🚫 Portfolio health check: HALTED")
        
        # Position sizing for each symbol
        if plan.symbols:
            account_value = health_data.get("account_equity", 100000) if health_result.get("success") else 100000
            for symbol in plan.symbols:
                position_result = self.skills.calculate_position(
                    symbol=symbol,
                    account_value=account_value,
                    risk_per_trade_pct=1.0
                )
                results["risk_checks"][f"{symbol}_position"] = position_result
        
        return results
    
    def _execute_trades(self, plan: TradePlan, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trades using high-speed agents"""
        results = {
            "phase": PlanningPhase.EXECUTION.value,
            "orders": [],
            "decision": "NO_TRADE"
        }
        
        ensemble_vote = analysis_result.get("ensemble_vote", {})
        
        # Use Go ADK for high-speed execution
        if self.adk_adapter and self.adk_adapter.enabled:
            for symbol, vote in ensemble_vote.items():
                if vote.get("consensus") == "BUY":
                    try:
                        # Use ADK for execution
                        adk_result = self.adk_adapter.evaluate(
                            symbols=[symbol],
                            context={
                                "plan_id": plan.plan_id,
                                "ensemble_vote": vote
                            }
                        )
                        results["orders"].append({
                            "symbol": symbol,
                            "agent": "go_adk",
                            "result": adk_result
                        })
                    except Exception as e:
                        logger.error(f"ADK execution failed for {symbol}: {e}")
        
        # Fallback to MCP orchestrator
        elif self.mcp_orchestrator:
            for symbol, vote in ensemble_vote.items():
                if vote.get("consensus") == "BUY":
                    try:
                        mcp_result = self.mcp_orchestrator.run_once(execute_orders=True)
                        results["orders"].append({
                            "symbol": symbol,
                            "agent": "mcp",
                            "result": mcp_result
                        })
                    except Exception as e:
                        logger.error(f"MCP execution failed for {symbol}: {e}")
        
        if results["orders"]:
            results["decision"] = "TRADE_EXECUTED"
        
        # Anomaly detection after execution
        for order in results["orders"]:
            if order.get("result", {}).get("execution"):
                exec_data = order["result"]["execution"]
                anomaly_result = self.skills.detect_execution_anomalies(
                    order_id=exec_data.get("order_id", "unknown"),
                    expected_price=exec_data.get("expected_price", 0),
                    actual_fill_price=exec_data.get("fill_price", 0),
                    quantity=exec_data.get("quantity", 0),
                    order_type=exec_data.get("order_type", "market"),
                    timestamp=datetime.now().isoformat()
                )
                order["anomaly_check"] = anomaly_result
        
        return results
    
    def _execute_audit(self, plan: TradePlan, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute audit phase"""
        results = {
            "phase": PlanningPhase.AUDIT.value,
            "performance_metrics": {},
            "git_commit": None
        }
        
        # Performance monitoring
        if self.skills.performance_monitor:
            perf_result = self.skills.get_performance_metrics(
                start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            results["performance_metrics"] = perf_result
        
        # Save audit trail
        audit_file = self.audit_dir / f"{plan.plan_id}_audit.json"
        audit_data = {
            "plan_id": plan.plan_id,
            "timestamp": datetime.now().isoformat(),
            "plan": asdict(plan),
            "execution_results": execution_results
        }
        with open(audit_file, "w") as f:
            json.dump(audit_data, f, indent=2, default=str)
        
        logger.info(f"📝 Audit trail saved: {audit_file}")
        
        return results
    
    def _save_plan(self, plan: TradePlan):
        """Save plan to persistent storage"""
        plan_file = self.plans_dir / f"{plan.plan_id}.json"
        with open(plan_file, "w") as f:
            json.dump(asdict(plan), f, indent=2, default=str)
    
    def _save_results(self, plan_id: str, results: Dict[str, Any]):
        """Save execution results"""
        results_file = self.plans_dir / f"{plan_id}_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
    
    def run_trading_cycle(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Run a complete trading cycle with planning-first approach
        
        Args:
            symbols: Symbols to trade
            
        Returns:
            Complete cycle results
        """
        logger.info("=" * 80)
        logger.info("ELITE TRADING CYCLE STARTING")
        logger.info("=" * 80)
        
        # Step 1: Create plan
        plan = self.create_trade_plan(symbols)
        
        # Step 2: Execute plan
        results = self.execute_plan(plan)
        
        logger.info("=" * 80)
        logger.info("ELITE TRADING CYCLE COMPLETE")
        logger.info("=" * 80)
        
        return results

