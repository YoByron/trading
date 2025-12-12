#!/usr/bin/env python3
"""Test the Dialogflow webhook locally without starting the server."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.dialogflow_webhook import handle_intent
from src.rag.unified_rag import UnifiedRAG

print("=" * 60)
print("Testing Dialogflow Webhook Handlers")
print("=" * 60)
print()

# Initialize RAG
rag = UnifiedRAG()
print(f"✅ RAG loaded with {rag.lessons_collection.count()} lessons")
print()

# Test each intent
intents_to_test = [
    ("lessons_learned", {}),
    ("system_health", {}),
    ("performance_metrics", {}),
]

for intent_name, params in intents_to_test:
    print(f"Testing intent: {intent_name}")
    print("-" * 60)

    response = handle_intent(intent_name, params, {"text": "test query"})

    print(response)
    print()
    print()

print("=" * 60)
print("✅ Webhook handlers working!")
print("=" * 60)
