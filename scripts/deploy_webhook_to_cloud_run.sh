#!/bin/bash
# Deploy Dialogflow webhook to Google Cloud Run

set -e

PROJECT_ID="igor-trading-2025-v2"
SERVICE_NAME="dialogflow-webhook"
REGION="us-central1"

echo "🚀 Deploying Dialogflow Webhook to Cloud Run"
echo "=============================================="
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Build container with Cloud Build
echo "📦 Building container..."
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Copy Dockerfile.webhook to Dockerfile for Cloud Build
cp Dockerfile.webhook Dockerfile

gcloud builds submit --tag $IMAGE_NAME .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --timeout 60 \
    --max-instances 3 \
    --set-env-vars "PYTHONUNBUFFERED=1"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Webhook URL: $SERVICE_URL/webhook"
echo ""
echo "📋 Next steps:"
echo "  1. Test webhook: curl $SERVICE_URL/"
echo "  2. Configure Dialogflow webhook with URL: $SERVICE_URL/webhook"
echo ""
