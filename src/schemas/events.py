from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(Enum):
    SIGNAL = "signal"
    DECISION = "decision"
    VALIDATION = "validation"
    EXECUTION = "execution"
    SETTLEMENT = "settlement"
    AUDIT = "audit"


@dataclass
class AuditEvent:
    """Base class for all auditable events in the system."""

    event_id: str
    trace_id: str  # Correlation ID linking signal -> decision -> execution
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_type: EventType = EventType.SIGNAL
    agent_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
