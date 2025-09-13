#!/bin/bash

# Fly.io deployment script for SABDA Scraper
set -e

echo "🚀 Deploying SABDA Scraper to Fly.io..."

# Check if Fly CLI is installed
if ! command -v flyctl &> /dev/null; then
    echo "Installing Fly CLI..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Login to Fly.io
echo "🔑 Login to Fly.io (browser will open)..."
flyctl auth login

# Launch the app (creates app if it doesn't exist)
echo "🚀 Launching app on Fly.io..."
flyctl launch --no-deploy

# Set secrets (sensitive environment variables)
echo "🔐 Setting secrets..."
flyctl secrets set SECRET_KEY=$(openssl rand -base64 32)

# Deploy
echo "📦 Deploying to Fly.io..."
flyctl deploy

# Show app status
echo "✅ Deployment completed!"
flyctl status
flyctl info

echo "🌐 Your app is available at: https://sabda-scraper-go.fly.dev"
echo "🔍 Health check: https://sabda-scraper-go.fly.dev/api/health"
