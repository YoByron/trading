import os

from dotenv import load_dotenv
from google.api_core.client_options import ClientOptions
from google.cloud import dialogflowcx_v3

# Load env
load_dotenv()

PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
LOCATION = os.getenv("DIALOGFLOW_LOCATION", "global")
AGENT_ID = os.getenv("DIALOGFLOW_AGENT_ID")


def get_client_options():
    if LOCATION != "global":
        api_endpoint = f"{LOCATION}-dialogflow.googleapis.com:443"
        return ClientOptions(api_endpoint=api_endpoint, quota_project_id=PROJECT_ID)
    return ClientOptions(api_endpoint="dialogflow.googleapis.com", quota_project_id=PROJECT_ID)


def inspect_agent():
    print(f"Inspecting Agent: {AGENT_ID}")

    intents_client = dialogflowcx_v3.IntentsClient(client_options=get_client_options())
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}"

    intents = intents_client.list_intents(parent=parent)

    for intent in intents:
        print(f"\n=== Intent: {intent.display_name} ===")
        print("Training Phrases:")
        for phrase in intent.training_phrases:
            parts = "".join([p.text for p in phrase.parts])
            print(f"  - {parts}")


if __name__ == "__main__":
    inspect_agent()
