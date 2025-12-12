from google.api_core.client_options import ClientOptions
from google.cloud import dialogflowcx_v3

# Hardcode the OLD project details from memory/summary
PROJECT_ID = "igor-trading-2025-v2"
LOCATION = "global"
AGENT_ID = "98373354-4197-4cb1-a7a0-1966ea6d27a7"


def get_client_options():
    return ClientOptions(api_endpoint="dialogflow.googleapis.com", quota_project_id=PROJECT_ID)


def inspect_agent():
    print(f"Inspecting Agent: {AGENT_ID} in {PROJECT_ID}")

    try:
        intents_client = dialogflowcx_v3.IntentsClient(client_options=get_client_options())
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}"

        intents = intents_client.list_intents(parent=parent)

        print(f"Found {len(list(intents))} intents.")
        # Reload iterator
        intents = intents_client.list_intents(parent=parent)

        for intent in intents:
            print(f"- {intent.display_name}")
            if intent.display_name == "capabilities.intent":
                print("  Phrases:")
                for phrase in intent.training_phrases:
                    parts = "".join([p.text for p in phrase.parts])
                    print(f"    - {parts}")

    except Exception as e:
        print(f"Failed to access {PROJECT_ID}: {e}")


if __name__ == "__main__":
    inspect_agent()
