#!/bin/bash

# Azure deployment script for SABDA Scraper
set -e

# Configuration
RESOURCE_GROUP="rg-sabda-scraper"
LOCATION="Southeast Asia"
WEB_APP_NAME="sabda-scraper-go"
SUBSCRIPTION_ID=""  # Add your subscription ID

echo "🚀 Starting Azure deployment for SABDA Scraper..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first:"
    echo "   brew install azure-cli"
    exit 1
fi

# Login to Azure (if not already logged in)
if ! az account show &> /dev/null; then
    echo "🔑 Logging in to Azure..."
    az login
fi

# Set subscription if provided
if [ -n "$SUBSCRIPTION_ID" ]; then
    echo "📋 Setting subscription to $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Create resource group
echo "📦 Creating resource group: $RESOURCE_GROUP"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION"

# Deploy infrastructure using Bicep
echo "🏗️  Deploying infrastructure..."
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file bicep/main.bicep \
    --parameters webAppName="$WEB_APP_NAME"

# Build and deploy the application
echo "🔨 Building Go application..."
go mod tidy
go build -o bin/server ./cmd/server

# Create deployment package
echo "📦 Creating deployment package..."
zip -r deployment.zip bin/ -x "*.git*"

# Deploy to App Service
echo "🚀 Deploying to Azure App Service..."
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$WEB_APP_NAME" \
    --src deployment.zip

# Get the app URL
APP_URL=$(az webapp show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$WEB_APP_NAME" \
    --query "defaultHostName" \
    --output tsv)

echo "✅ Deployment completed successfully!"
echo "🌐 Your app is available at: https://$APP_URL"
echo "🔍 Health check: https://$APP_URL/api/health"

# Clean up
rm -f deployment.zip

echo "🎉 Migration from Render to Azure completed!"
