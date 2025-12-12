import os
import sys

from dotenv import load_dotenv

# Load env before importing client
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.agents.dialogflow_client import DialogflowClient
except ImportError:
    print("Could not import DialogflowClient. Check path.")
    sys.exit(1)


def main():
    try:
        # Initialize client (reads from .env)
        client = DialogflowClient()
        print(f"Initialized client for project: {client.project_id}")

        # Test interaction
        session_id = "test-verification-session"
        query_text = "what did you learn"
        response = client.detect_intent(session_id, query_text)

        print("\n✅ Connectivity Verified!")
        print(f"Sent: {query_text}")
        print(f"Received: {response}")

    except Exception as e:
        print(f"\n❌ Connectivity Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
