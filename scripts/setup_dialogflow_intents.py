#!/usr/bin/env python3
"""
Setup Dialogflow CX Intents for Trading Agent

Creates essential intents for the trading system:
- Lessons learned queries
- Performance metrics
- Trade status
- System health
"""

import os

from google.cloud.dialogflowcx_v3 import Intent, IntentsClient
from google.cloud.dialogflowcx_v3.types import Intent


def create_intent(client, parent: str, display_name: str, training_phrases: list, responses: list):
    """Create a single intent with training phrases and responses."""

    # Build training phrases
    training_phrase_parts = [
        Intent.TrainingPhrase(parts=[Intent.TrainingPhrase.Part(text=phrase)], repeat_count=1)
        for phrase in training_phrases
    ]

    intent = Intent(
        display_name=display_name,
        training_phrases=training_phrase_parts,
        description=f"Handles {display_name} queries",
    )

    request = {
        "parent": parent,
        "intent": intent,
    }

    try:
        response = client.create_intent(request=request)
        print(f"✅ Created intent: {display_name}")
        return response
    except Exception as e:
        print(f"❌ Failed to create intent {display_name}: {e}")
        return None


def setup_intents():
    """Setup all trading-related intents."""

    project_id = os.getenv("DIALOGFLOW_PROJECT_ID")
    location = os.getenv("DIALOGFLOW_LOCATION", "global")
    agent_id = os.getenv("DIALOGFLOW_AGENT_ID")

    if not all([project_id, location, agent_id]):
        print("❌ Missing Dialogflow configuration. Check .env file.")
        return

    print(f"🚀 Setting up intents for agent: {agent_id}")
    print(f"   Project: {project_id}")
    print(f"   Location: {location}")
    print()

    client = IntentsClient()
    parent = f"projects/{project_id}/locations/{location}/agents/{agent_id}"

    # Intent 1: Lessons Learned
    create_intent(
        client=client,
        parent=parent,
        display_name="lessons_learned",
        training_phrases=[
            "what lessons have we learned",
            "show me lessons learned",
            "what have we learned",
            "lessons from trading",
            "what mistakes did we make",
            "trading lessons",
            "show lessons",
        ],
        responses=["I'll fetch the latest lessons learned from our trading experience."],
    )

    # Intent 2: Performance Metrics
    create_intent(
        client=client,
        parent=parent,
        display_name="performance_metrics",
        training_phrases=[
            "how are we performing",
            "show performance",
            "what's our win rate",
            "trading performance",
            "show me metrics",
            "how much profit",
            "what's the sharpe ratio",
            "performance stats",
        ],
        responses=["Let me get the latest performance metrics for you."],
    )

    # Intent 3: Trade Status
    create_intent(
        client=client,
        parent=parent,
        display_name="trade_status",
        training_phrases=[
            "any trades today",
            "did we trade",
            "show trades",
            "what trades executed",
            "today's trades",
            "trade history",
            "recent trades",
        ],
        responses=["Let me check today's trading activity."],
    )

    # Intent 4: System Health
    create_intent(
        client=client,
        parent=parent,
        display_name="system_health",
        training_phrases=[
            "system status",
            "is the system running",
            "health check",
            "any errors",
            "system health",
            "is everything working",
        ],
        responses=["Let me check the system health status."],
    )

    # Intent 5: Next Trade
    create_intent(
        client=client,
        parent=parent,
        display_name="next_trade",
        training_phrases=[
            "when is the next trade",
            "next trade time",
            "when will we trade",
            "trading schedule",
            "next execution",
        ],
        responses=["Let me check the next scheduled trade time."],
    )

    print()
    print("✅ Intent setup complete!")
    print(
        f"🌐 View your agent: https://dialogflow.cloud.google.com/cx/projects/{project_id}/locations/{location}/agents/{agent_id}"
    )


if __name__ == "__main__":
    setup_intents()
