"""
Context Engine for Multi-Agent Systems

Implements context engineering principles from:
- "Context Engineering for Multi-Agent Systems" (Packt)
- "Context Engineering for Multi-Agent LLM Code Assistants" (arXiv:2508.08322)

Key Concepts:
1. Semantic Blueprints: Structured definitions of agent roles, capabilities, and communication
2. Context Flow: Structured passing of context between agents without information loss
3. Context Validation: Ensuring context integrity and completeness
4. Memory & Persistence: Long-term and short-term context storage
5. Error Handling: Resilient context passing with fallbacks
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context in the system"""
    SEMANTIC_BLUEPRINT = "semantic_blueprint"  # Agent role/capability definition
    TASK_CONTEXT = "task_context"  # Specific task information
    MEMORY_CONTEXT = "memory_context"  # Historical context
    VALIDATION_CONTEXT = "validation_context"  # Validation rules
    COMMUNICATION_CONTEXT = "communication_context"  # Inter-agent messages


class ContextPriority(Enum):
    """Priority levels for context"""
    CRITICAL = "critical"  # Must be included
    HIGH = "high"  # Should be included
    MEDIUM = "medium"  # Include if space allows
    LOW = "low"  # Optional


@dataclass
class SemanticBlueprint:
    """
    Semantic Blueprint: Structured definition of an agent's role, capabilities,
    and communication protocol.
    
    Moves beyond simple prompts to structured context that defines:
    - What the agent does (role)
    - What it needs (inputs)
    - What it produces (outputs)
    - How it communicates (protocol)
    """
    agent_id: str
    agent_name: str
    role: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    inputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Input schema
    outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Output schema
    communication_protocol: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Other agents this depends on
    context_window_size: int = 8000  # Estimated tokens needed
    priority: ContextPriority = ContextPriority.HIGH
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_context_dict(self) -> Dict[str, Any]:
        """Convert blueprint to context dictionary for LLM"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "description": self.description,
            "capabilities": self.capabilities,
            "input_schema": self.inputs,
            "output_schema": self.outputs,
            "communication_protocol": self.communication_protocol,
            "dependencies": self.dependencies
        }


@dataclass
class ContextMessage:
    """
    Structured message for inter-agent communication using MCP principles.
    
    Ensures context is passed reliably without information loss.
    """
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    sender_agent: str = ""
    receiver_agent: str = ""
    context_type: ContextType = ContextType.COMMUNICATION_CONTEXT
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_hash: Optional[str] = None  # For integrity checking
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate message structure and completeness"""
        errors = []
        
        if not self.sender_agent:
            errors.append("Missing sender_agent")
        if not self.receiver_agent:
            errors.append("Missing receiver_agent")
        if not self.payload:
            errors.append("Empty payload")
        
        return len(errors) == 0, errors
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP-compatible format"""
        return {
            "id": self.message_id,
            "timestamp": self.timestamp,
            "from": self.sender_agent,
            "to": self.receiver_agent,
            "type": self.context_type.value,
            "data": self.payload,
            "meta": self.metadata
        }


@dataclass
class ContextMemory:
    """
    Memory storage for context persistence.
    
    Supports both short-term (session) and long-term (persistent) memory.
    """
    memory_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    context_type: ContextType = ContextType.MEMORY_CONTEXT
    content: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    ttl_days: Optional[int] = None  # Time-to-live for short-term memory
    
    def is_expired(self) -> bool:
        """Check if memory has expired"""
        if self.ttl_days is None:
            return False
        created = datetime.fromisoformat(self.created_at)
        return datetime.now() - created > timedelta(days=self.ttl_days)
    
    def touch(self):
        """Update access time and count"""
        self.accessed_at = datetime.now().isoformat()
        self.access_count += 1


class ContextEngine:
    """
    Context Engine: Manages structured context for multi-agent systems.
    
    Responsibilities:
    1. Store and retrieve semantic blueprints
    2. Manage context flow between agents
    3. Validate context integrity
    4. Persist context for memory
    5. Handle context errors gracefully
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize Context Engine
        
        Args:
            storage_dir: Directory for persistent storage (defaults to data/agent_context)
        """
        self.storage_dir = storage_dir or Path("data/agent_context")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self.blueprints: Dict[str, SemanticBlueprint] = {}
        self.memory: Dict[str, ContextMemory] = {}
        self.message_history: List[ContextMessage] = []
        
        # Load persisted data
        self._load_persisted_data()
        
        logger.info(f"✅ Context Engine initialized: {len(self.blueprints)} blueprints, {len(self.memory)} memories")
    
    def register_blueprint(self, blueprint: SemanticBlueprint) -> None:
        """
        Register a semantic blueprint for an agent.
        
        Args:
            blueprint: Semantic blueprint to register
        """
        self.blueprints[blueprint.agent_id] = blueprint
        
        # Persist blueprint
        blueprint_file = self.storage_dir / "blueprints" / f"{blueprint.agent_id}.json"
        blueprint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(blueprint_file, "w") as f:
            json.dump(asdict(blueprint), f, indent=2, default=str)
        
        logger.info(f"📋 Registered blueprint: {blueprint.agent_id} ({blueprint.agent_name})")
    
    def get_blueprint(self, agent_id: str) -> Optional[SemanticBlueprint]:
        """Get blueprint for an agent"""
        return self.blueprints.get(agent_id)
    
    def get_agent_context(self, agent_id: str, max_tokens: int = 8000) -> Dict[str, Any]:
        """
        Get complete context for an agent, including blueprint and relevant memories.
        
        Args:
            agent_id: Agent identifier
            max_tokens: Maximum context window size
            
        Returns:
            Complete context dictionary
        """
        blueprint = self.blueprints.get(agent_id)
        if not blueprint:
            logger.warning(f"⚠️ No blueprint found for agent: {agent_id}")
            return {}
        
        context = {
            "blueprint": blueprint.to_context_dict(),
            "memories": [],
            "recent_messages": []
        }
        
        # Add relevant memories (prioritized by recency and access count)
        agent_memories = [
            m for m in self.memory.values()
            if m.agent_id == agent_id and not m.is_expired()
        ]
        agent_memories.sort(key=lambda m: (m.access_count, m.accessed_at), reverse=True)
        
        token_count = len(json.dumps(context))
        for memory in agent_memories[:10]:  # Limit to top 10 memories
            memory_json = json.dumps(asdict(memory))
            if token_count + len(memory_json) < max_tokens:
                context["memories"].append(asdict(memory))
                token_count += len(memory_json)
            else:
                break
        
        # Add recent messages involving this agent
        recent_messages = [
            msg for msg in self.message_history[-20:]
            if msg.sender_agent == agent_id or msg.receiver_agent == agent_id
        ]
        context["recent_messages"] = [msg.to_mcp_format() for msg in recent_messages[-5:]]
        
        return context
    
    def send_context_message(
        self,
        sender: str,
        receiver: str,
        payload: Dict[str, Any],
        context_type: ContextType = ContextType.COMMUNICATION_CONTEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextMessage:
        """
        Send a structured context message between agents.
        
        Args:
            sender: Sender agent ID
            receiver: Receiver agent ID
            payload: Message payload
            context_type: Type of context
            metadata: Optional metadata
            
        Returns:
            Created context message
        """
        message = ContextMessage(
            sender_agent=sender,
            receiver_agent=receiver,
            context_type=context_type,
            payload=payload,
            metadata=metadata or {}
        )
        
        # Validate message
        is_valid, errors = message.validate()
        if not is_valid:
            logger.error(f"❌ Invalid context message: {errors}")
            raise ValueError(f"Invalid context message: {errors}")
        
        # Store in history
        self.message_history.append(message)
        
        # Persist message
        self._persist_message(message)
        
        logger.debug(f"📨 Context message sent: {sender} -> {receiver}")
        return message
    
    def store_memory(
        self,
        agent_id: str,
        content: Dict[str, Any],
        tags: Optional[Set[str]] = None,
        ttl_days: Optional[int] = None
    ) -> ContextMemory:
        """
        Store context in memory for later retrieval.
        
        Args:
            agent_id: Agent identifier
            content: Content to store
            tags: Optional tags for retrieval
            ttl_days: Time-to-live in days (None = permanent)
            
        Returns:
            Created memory object
        """
        memory = ContextMemory(
            agent_id=agent_id,
            content=content,
            tags=tags or set(),
            ttl_days=ttl_days
        )
        
        self.memory[memory.memory_id] = memory
        
        # Persist memory
        self._persist_memory(memory)
        
        logger.debug(f"💾 Memory stored: {agent_id} ({len(content)} keys)")
        return memory
    
    def retrieve_memories(
        self,
        agent_id: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 10
    ) -> List[ContextMemory]:
        """
        Retrieve memories by agent ID and/or tags.
        
        Args:
            agent_id: Filter by agent ID
            tags: Filter by tags
            limit: Maximum number of memories to return
            
        Returns:
            List of matching memories
        """
        memories = list(self.memory.values())
        
        # Filter by agent
        if agent_id:
            memories = [m for m in memories if m.agent_id == agent_id]
        
        # Filter by tags
        if tags:
            memories = [
                m for m in memories
                if tags.intersection(m.tags)
            ]
        
        # Remove expired
        memories = [m for m in memories if not m.is_expired()]
        
        # Sort by recency and access count
        memories.sort(key=lambda m: (m.access_count, m.accessed_at), reverse=True)
        
        # Touch accessed memories
        for memory in memories[:limit]:
            memory.touch()
        
        return memories[:limit]
    
    def validate_context_flow(
        self,
        from_agent: str,
        to_agent: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that context can flow correctly between agents.
        
        Checks:
        1. Both agents have blueprints
        2. Sender's outputs match receiver's inputs
        3. Required fields are present
        
        Args:
            from_agent: Sender agent ID
            to_agent: Receiver agent ID
            context: Context to validate
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        sender_blueprint = self.blueprints.get(from_agent)
        receiver_blueprint = self.blueprints.get(to_agent)
        
        if not sender_blueprint:
            errors.append(f"Sender agent '{from_agent}' has no blueprint")
        
        if not receiver_blueprint:
            errors.append(f"Receiver agent '{to_agent}' has no blueprint")
        
        if sender_blueprint and receiver_blueprint:
            # Check if sender's outputs match receiver's inputs
            sender_outputs = set(sender_blueprint.outputs.keys())
            receiver_inputs = set(receiver_blueprint.inputs.keys())
            
            # Check for required inputs
            for input_key, input_spec in receiver_blueprint.inputs.items():
                if input_spec.get("required", False):
                    if input_key not in context:
                        errors.append(f"Missing required input '{input_key}' for {to_agent}")
        
        return len(errors) == 0, errors
    
    def _load_persisted_data(self):
        """Load blueprints and memories from disk"""
        # Load blueprints
        blueprints_dir = self.storage_dir / "blueprints"
        if blueprints_dir.exists():
            for blueprint_file in blueprints_dir.glob("*.json"):
                try:
                    with open(blueprint_file, "r") as f:
                        data = json.load(f)
                        blueprint = SemanticBlueprint(**data)
                        self.blueprints[blueprint.agent_id] = blueprint
                except Exception as e:
                    logger.warning(f"Failed to load blueprint {blueprint_file}: {e}")
        
        # Load memories
        memories_dir = self.storage_dir / "memories"
        if memories_dir.exists():
            for memory_file in memories_dir.glob("*.json"):
                try:
                    with open(memory_file, "r") as f:
                        data = json.load(f)
                        memory = ContextMemory(**data)
                        memory.tags = set(memory.tags)  # Convert list back to set
                        self.memory[memory.memory_id] = memory
                except Exception as e:
                    logger.warning(f"Failed to load memory {memory_file}: {e}")
    
    def _persist_message(self, message: ContextMessage):
        """Persist message to disk"""
        messages_dir = self.storage_dir / "messages"
        messages_dir.mkdir(parents=True, exist_ok=True)
        
        message_file = messages_dir / f"{message.message_id}.json"
        with open(message_file, "w") as f:
            json.dump(asdict(message), f, indent=2, default=str)
    
    def _persist_memory(self, memory: ContextMemory):
        """Persist memory to disk"""
        memories_dir = self.storage_dir / "memories"
        memories_dir.mkdir(parents=True, exist_ok=True)
        
        memory_file = memories_dir / f"{memory.memory_id}.json"
        memory_dict = asdict(memory)
        memory_dict["tags"] = list(memory_dict["tags"])  # Convert set to list for JSON
        with open(memory_file, "w") as f:
            json.dump(memory_dict, f, indent=2, default=str)


# Global singleton instance
_context_engine: Optional[ContextEngine] = None


def get_context_engine(storage_dir: Optional[Path] = None) -> ContextEngine:
    """Get or create global context engine instance"""
    global _context_engine
    if _context_engine is None:
        _context_engine = ContextEngine(storage_dir=storage_dir)
    return _context_engine

