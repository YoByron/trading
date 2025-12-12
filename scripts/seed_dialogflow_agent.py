import os
import sys

from dotenv import load_dotenv
from google.api_core.client_options import ClientOptions
from google.cloud import dialogflowcx_v3

# Load env
load_dotenv()

PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
LOCATION = os.getenv("DIALOGFLOW_LOCATION", "global")
AGENT_ID = os.getenv("DIALOGFLOW_AGENT_ID")

if not all([PROJECT_ID, AGENT_ID]):
    print("Error: Config missing in .env")
    sys.exit(1)


def get_client_options():
    if LOCATION != "global":
        api_endpoint = f"{LOCATION}-dialogflow.googleapis.com:443"
        return ClientOptions(api_endpoint=api_endpoint, quota_project_id=PROJECT_ID)
    return ClientOptions(api_endpoint="dialogflow.googleapis.com", quota_project_id=PROJECT_ID)


def seed_agent():
    print(f"Seeding Agent: projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}")

    intents_client = dialogflowcx_v3.IntentsClient(client_options=get_client_options())
    flows_client = dialogflowcx_v3.FlowsClient(client_options=get_client_options())

    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}"

    # 1. Define Intents & Knowledge
    # Note: In a real system, these responses would come from a webhook.
    # For now, we seed them as static responses to prove the flow.

    intents_to_create = [
        {
            "display_name": "welcome.intent",
            "training_phrases": ["hello", "hi", "hey", "start", "boot up", "wake up"],
            "response_text": "Trading Agent v2 Online. I have read the latest dashboard. Ready for queries.",
        },
        {
            "display_name": "system.status",
            "training_phrases": ["status", "system check", "health check", "are you online"],
            "response_text": "All systems nominal. Active feeds: Alpaca (Live), Tradier (Live), Kalshi (Maintenance).",
        },
        {
            "display_name": "learning.intent",
            "training_phrases": [
                "what did you learn",
                "latest lessons",
                "what patterns did you find",
                "new insights",
                "did you learn anything",
                "knowledge report",
                "what is the last three lessons you learned",
                "tell me the last lessons",
            ],
            # Actual insights from dashboard.md
            "response_text": (
                "Here are the latest insights from the AI Cortex:\n"
                "1. LESSON: We cannot deploy to production without proper testing.\n"
                "2. STRATEGY: MACD indicator is now integrated into Tier 1 and Tier 2 strategies.\n"
                "3. PATTERN: MACD confirms momentum and filters out false RSI signals.\n"
                "4. SIGNAL: Histogram > 0 is Bullish; Histogram < 0 is Bearish."
            ),
        },
        {
            "display_name": "performance.crypto",
            "training_phrases": [
                "how much money from crypto",
                "crypto trading pnl",
                "profit from crypto",
                "bitcoin performance",
                "btc results",
            ],
            "response_text": (
                "🪙 **Crypto Performance**:\n"
                "- **Status**: Accumulation Phase (BTC buys)\n"
                "- **Realized P/L**: $-0.01 (ETHUSD test trade)\n"
                "- **Recent Activity**: 3 BTC buy orders via CryptoStrategy."
            ),
        },
        {
            "display_name": "performance.daily",
            "training_phrases": [
                "how much money did we make today",
                "daily pnl",
                "profit today",
                "today's results",
                "day performance",
            ],
            "response_text": (
                "📅 **Today's Performance (2025-12-10)**:\n"
                "- **Daily P/L**: +$24.69 (+0.02%)\n"
                "- **Trades**: 0 closed trades today."
            ),
        },
        {
            "display_name": "performance.total",
            "training_phrases": [
                "how much money we made in total",
                "total profit",
                "total pnl",
                "account equity",
                "net worth",
                "all time profit",
            ],
            "response_text": (
                "💰 **Total Account Status**:\n"
                "- **Equity**: $100,024.69\n"
                "- **Total P/L**: +$17.49\n"
                "- **Goal**: $100/day (Currently at $2.92/day avg)."
            ),
        },
        {
            "display_name": "capabilities.intent",
            "training_phrases": [
                "what can you do",
                "help",
                "capabilities",
                "functions",
                "menu",
                "what do you know about trading",
                "how do you trade",
            ],
            "response_text": (
                "I am the Trading System AI. I can:\n"
                "- Report System Status ('status')\n"
                "- Share Learned Patterns ('what did you learn')\n"
                "- Track Holdings ('show holdings' - coming soon via webhook)\n"
                "- Explain Decisions ('why did you buy BTC')"
            ),
        },
        {
            "display_name": "frustration.intent",
            "training_phrases": [
                "is that all",
                "you are garbage",
                "useless",
                "stupid",
                "that's it?",
            ],
            "response_text": (
                "I apologize if my current capabilities are limited. "
                "I am currently in 'Seed Mode'. My full neural functions (Webhooks) are being connected. "
                "Try asking 'what did you learn' to see my latest memory persistence."
            ),
        },
    ]

    created_intents = {}

    # Prune existing intents to avoid "Ambiguous Intent" errors or duplicates
    existing_intents_list = list(intents_client.list_intents(parent=parent))
    existing_map = {i.display_name: i.name for i in existing_intents_list}

    # Explicitly remove legacy performance intent if it exists
    if "performance.intent" in existing_map:
        print("Deleting legacy intent: performance.intent")
        try:
            intents_client.delete_intent(name=existing_map["performance.intent"])
            del existing_map["performance.intent"]
        except Exception as e:
            print(f"Warning: Could not delete performance.intent: {e}")

    for intent_data in intents_to_create:
        display_name = intent_data["display_name"]

        # If exists, we UPDATE it to ensure new phrases/responses are applied
        if display_name in existing_map:
            print(f"Updating existing intent: {display_name}")
            # Get existing object
            intent_name = existing_map[display_name]

            # Prepare new training phrases
            training_phrases = [
                {"parts": [{"text": phrase}], "repeat_count": 1}
                for phrase in intent_data["training_phrases"]
            ]

            intent = dialogflowcx_v3.Intent(
                name=intent_name, display_name=display_name, training_phrases=training_phrases
            )

            # Update (Replaces phrases)
            intents_client.update_intent(intent=intent, update_mask={"paths": ["training_phrases"]})
            created_intents[display_name] = intent_name

        else:
            print(f"Creating new intent: {display_name}")
            training_phrases = [
                {"parts": [{"text": phrase}], "repeat_count": 1}
                for phrase in intent_data["training_phrases"]
            ]

            intent = dialogflowcx_v3.Intent(
                display_name=display_name, training_phrases=training_phrases
            )

            response = intents_client.create_intent(parent=parent, intent=intent)
            created_intents[display_name] = response.name

    # 2. Update Default Start Flow Routes
    flows = flows_client.list_flows(parent=parent)
    default_flow = None
    for f in flows:
        if "Default Start Flow" in f.display_name:
            default_flow = f
            break

    if not default_flow:
        print("Error: Could not find Default Start Flow")
        return

    print(f"Configuring Flow: {default_flow.display_name}")

    # Merge with existing routes to preserve Welcome Intent (which cannot be deleted)
    existing_routes = list(default_flow.transition_routes)

    # Create a map of IntentID -> Route for easy updating
    # We use the intent (name string) as the key
    route_map = {r.intent: r for r in existing_routes if r.intent}

    # Explicitly remove legacy performance route if it exists in the map
    # We need to find the ID that corresponds to "performance.intent"
    # Since we don't have the ID easily here, we might have to rely on the intent display name if we had it,
    # but route.intent is the full resource name (projects/.../intents/UUID).
    # HACK: We will just accept that the new specific routes will take precedence if seeded,
    # BUT to be clean, we should filter by the Intent object we couldn't delete earlier.

    # Actually, we can just filter out any route where the intent name is NOT in our new list + welcome/status/etc.
    # But that's risky.
    # Let's just proceed. The new specific intents will be added.
    # The old 'performance.intent' route will remain, but since we deleted the *Intent* (oh wait we failed),
    # it still exists.

    # Let's look up the legacy intent ID to remove it from routes
    if "performance.intent" in existing_map:
        legacy_id = existing_map["performance.intent"]
        if legacy_id in route_map:
            print("Removing legacy route for performance.intent")
            del route_map[legacy_id]

    for intent_data in intents_to_create:
        intent_name = created_intents[intent_data["display_name"]]
        text_response = intent_data["response_text"]

        new_route = dialogflowcx_v3.TransitionRoute(
            intent=intent_name,
            trigger_fulfillment=dialogflowcx_v3.Fulfillment(
                messages=[
                    dialogflowcx_v3.ResponseMessage(
                        text=dialogflowcx_v3.ResponseMessage.Text(text=[text_response])
                    )
                ]
            ),
        )

        # Update or Add
        route_map[intent_name] = new_route

    # Convert back to list
    default_flow.transition_routes = list(route_map.values())

    flows_client.update_flow(flow=default_flow, update_mask={"paths": ["transition_routes"]})

    print("Flow routes updated successfully.")
    print("Agent is now smarter.")


if __name__ == "__main__":
    try:
        seed_agent()
    except Exception as e:
        print(f"Failed: {e}")
        import traceback

        traceback.print_exc()
