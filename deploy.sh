#!/bin/bash

# Cloud Run Deployment Script for HWDC 2025 MCP League
# This script deploys the application to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 HWDC 2025 MCP League - Cloud Run Deployment${NC}"
echo "=================================================="

# Check if required environment variables are set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️  GCP_PROJECT_ID not set. Please enter your GCP Project ID:${NC}"
    read -r GCP_PROJECT_ID
    export GCP_PROJECT_ID
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set. Please enter your OpenAI API key:${NC}"
    read -r OPENAI_API_KEY
    export OPENAI_API_KEY
fi

# Configuration
SERVICE_NAME="hwdc-2025-mcp-league"
REGION="asia-east1"
IMAGE_NAME="gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME"

echo ""
echo -e "${GREEN}📋 Deployment Configuration:${NC}"
echo "  Project ID: $GCP_PROJECT_ID"
echo "  Service Name: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Image: $IMAGE_NAME"
echo ""

# Confirm deployment
read -p "Do you want to proceed with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 1
fi

# Set GCP project
echo -e "${GREEN}🔧 Setting GCP project...${NC}"
gcloud config set project "$GCP_PROJECT_ID"

# Enable required APIs
echo -e "${GREEN}🔧 Enabling required GCP APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push image
echo -e "${GREEN}🏗️  Building Docker image...${NC}"
docker build -t "$IMAGE_NAME:latest" .

echo -e "${GREEN}📤 Pushing image to GCR...${NC}"
docker push "$IMAGE_NAME:latest"

# Deploy to Cloud Run
echo -e "${GREEN}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME:latest" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --set-env-vars "ENVIRONMENT=production,HOST=0.0.0.0,PORT=8000,LOG_LEVEL=INFO,ENABLE_MCP_SYSTEM=true" \
    --set-secrets "OPENAI_API_KEY=OPENAI_API_KEY:latest"

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo "=================================================="
echo -e "${GREEN}🌐 Service URL: ${NC}$SERVICE_URL"
echo -e "${GREEN}📊 Health Check: ${NC}$SERVICE_URL/health"
echo -e "${GREEN}📚 API Docs: ${NC}$SERVICE_URL/docs"
echo ""
echo -e "${YELLOW}Note: Make sure to create the OPENAI_API_KEY secret in Secret Manager:${NC}"
echo "  gcloud secrets create OPENAI_API_KEY --data-file=- <<< \"\$OPENAI_API_KEY\""
echo ""
