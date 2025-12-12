#!/bin/bash
# setup_dialogflow_project.sh
#
# Usage: ./setup_dialogflow_project.sh [PROJECT_ID]
#
# Helper script to create a new Google Cloud Project and enable Dialogflow CX.
# Requires 'gcloud' CLI to be installed and authenticated.

set -e

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
  read -p "Enter new Google Cloud Project ID (e.g., trading-agent-v1): " PROJECT_ID
fi

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Project ID is required."
    exit 1
fi

echo "Creating project: $PROJECT_ID..."
gcloud projects create "$PROJECT_ID" --name="Trading Agent Dialogflow"

echo "Setting default project..."
gcloud config set project "$PROJECT_ID"

echo "Enabling Dialogflow API..."
gcloud services enable dialogflow.googleapis.com

echo "Enabling Cloud Resource Manager API (required for some bindings)..."
gcloud services enable cloudresourcemanager.googleapis.com

echo "Creating Dialogflow CX Agent (default location: global)..."
# Note: Creating the actual agent via CLI is complex and often requires a specific flow.
# We will just ensure the API is enabled so the user can create the agent in the console or via Terraform later if needed.
# But we can try to create a basic one.

ACCESS_TOKEN=$(gcloud auth print-access-token)
curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://dialogflow.googleapis.com/v3/projects/$PROJECT_ID/locations/global/agents" \
  -d '{
    "displayName": "TradingAgent",
    "defaultLanguageCode": "en",
    "timeZone": "America/New_York"
  }' > agent_creation.json

AGENT_NAME=$(grep -o '"name": "[^"]*' agent_creation.json | grep -o '[^"]*$' | head -n1)
AGENT_ID=$(basename "$AGENT_NAME")

rm agent_creation.json

echo "Done!"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Agent ID: $AGENT_ID"
echo ""
echo "Please update your .env file:"
echo "DIALOGFLOW_PROJECT_ID=$PROJECT_ID"
echo "DIALOGFLOW_AGENT_ID=$AGENT_ID"
