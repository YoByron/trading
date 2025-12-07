"""Mental Toughness Coaching Module.

Implements Steve Siebold's "177 Mental Toughness Secrets of the World Class"
principles adapted for algorithmic trading systems.

The coach provides real-time psychological interventions, tracks emotional
state, and helps the trading system maintain world-class mental discipline.
"""

from .mental_toughness_coach import MentalToughnessCoach
from .psychology_state import PsychologyState, EmotionalZone
from .interventions import CoachingIntervention, InterventionType

__all__ = [
    "MentalToughnessCoach",
    "PsychologyState",
    "EmotionalZone",
    "CoachingIntervention",
    "InterventionType",
]
