#!/bin/bash
# Start Dialogflow webhook server and expose with ngrok

echo "🚀 Starting Dialogflow Webhook Server"
echo "======================================"
echo ""

# Start the webhook server in background
echo "Starting FastAPI webhook on port 8080..."
.venv/bin/python3 src/agents/dialogflow_webhook.py > /tmp/dialogflow_webhook.log 2>&1 &
WEBHOOK_PID=$!
echo "Webhook PID: $WEBHOOK_PID"
echo $WEBHOOK_PID > /tmp/dialogflow_webhook.pid

# Wait for server to start
sleep 3

# Test webhook
echo ""
echo "Testing webhook..."
curl -s http://localhost:8080/ | python3 -m json.tool

echo ""
echo ""
echo "✅ Webhook running on http://localhost:8080"
echo "📋 Logs: tail -f /tmp/dialogflow_webhook.log"
echo "🛑 Stop: kill \$(cat /tmp/dialogflow_webhook.pid)"
echo ""

if command -v ngrok &> /dev/null; then
    echo "🌐 Starting ngrok tunnel..."
    ngrok http 8080 --log=stdout > /tmp/ngrok.log 2>&1 &
    NGROK_PID=$!
    echo $NGROK_PID > /tmp/ngrok.pid

    sleep 3

    # Get ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)

    if [ -n "$NGROK_URL" ]; then
        echo ""
        echo "✅ Ngrok tunnel active!"
        echo "🌐 Public URL: $NGROK_URL"
        echo ""
        echo "📋 Configure Dialogflow webhook:"
        echo "   1. Go to: https://dialogflow.cloud.google.com/cx/projects/igor-trading-2025-v2/locations/global/agents/98373354-4197-4cb1-a7a0-1966ea6d27a7/flows"
        echo "   2. Click 'Webhooks' in left sidebar"
        echo "   3. Create webhook with URL: $NGROK_URL/webhook"
        echo ""
        echo "   OR run this command:"
        echo "   gcloud dialogflow-cx webhooks create --agent=98373354-4197-4cb1-a7a0-1966ea6d27a7 \\"
        echo "     --location=global --project=igor-trading-2025-v2 \\"
        echo "     --display-name='Trading RAG Webhook' \\"
        echo "     --uri='$NGROK_URL/webhook'"
        echo ""
    else
        echo "⚠️  Could not get ngrok URL. Check ngrok setup."
    fi
else
    echo "⚠️  ngrok not installed. Webhook only available locally."
    echo "   Install: brew install ngrok"
fi

echo ""
echo "Press Ctrl+C to stop both services"
wait
