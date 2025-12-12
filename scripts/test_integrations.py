#!/usr/bin/env python3
"""Test Dialogflow and Langsmith integrations"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langsmith import Client as LangsmithClient
from src.agents.dialogflow_client import DialogflowClient


def test_dialogflow():
    """Test Dialogflow CX integration"""
    print("🔍 Testing Dialogflow CX...")
    print()

    try:
        client = DialogflowClient()
        print("✅ Dialogflow client initialized")
        print(f"   Project: {client.project_id}")
        print(f"   Agent: {client.agent_id}")
        print()

        # Test query
        session_id = "test-session-123"
        response = client.detect_intent(session_id=session_id, text="what lessons have we learned")

        print("📝 Test Query: 'what lessons have we learned'")
        print(f"🤖 Response: {response}")
        print()

        return True

    except Exception as e:
        print(f"❌ Dialogflow test failed: {e}")
        print()
        return False


def test_langsmith():
    """Test Langsmith integration"""
    print("🔍 Testing Langsmith...")
    print()

    try:
        # Check API key
        api_key = os.getenv("LANGSMITH_API_KEY")
        if not api_key:
            print("❌ LANGSMITH_API_KEY not set in .env")
            return False

        client = LangsmithClient()
        print("✅ Langsmith client initialized")
        print(f"   Endpoint: {os.getenv('LANGSMITH_ENDPOINT')}")
        print(f"   Project: {os.getenv('LANGSMITH_PROJECT')}")
        print()

        # Test by creating a simple trace
        from langsmith.run_helpers import traceable

        @traceable(name="test_trace")
        def test_function():
            return "Langsmith is working!"

        result = test_function()
        print("📊 Created test trace")
        print("🌐 View dashboard: https://smith.langchain.com")
        print()

        return True

    except Exception as e:
        print(f"❌ Langsmith test failed: {e}")
        print()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Integration Tests")
    print("=" * 60)
    print()

    # Load .env
    from dotenv import load_dotenv

    load_dotenv()

    dialogflow_ok = test_dialogflow()
    langsmith_ok = test_langsmith()

    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Dialogflow: {'✅ PASS' if dialogflow_ok else '❌ FAIL'}")
    print(f"Langsmith:  {'✅ PASS' if langsmith_ok else '❌ FAIL'}")
    print()

    if dialogflow_ok and langsmith_ok:
        print("🎉 All integrations working!")
        sys.exit(0)
    else:
        print("⚠️  Some integrations failed")
        sys.exit(1)
