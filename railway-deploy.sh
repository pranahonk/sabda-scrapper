#!/bin/bash

# Railway deployment script for SABDA Scraper
set -e

echo "🚀 Deploying SABDA Scraper to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔑 Login to Railway (browser will open)..."
railway login

# Initialize Railway project
echo "📦 Initializing Railway project..."
railway init

# Set environment variables
echo "⚙️  Setting environment variables..."
railway variables set PORT=8080
railway variables set SECRET_KEY=$(openssl rand -base64 32)
railway variables set FLUTTER_API_KEY=sabda_flutter_2025_secure_key
railway variables set MOBILE_API_KEY=sabda_mobile_2025_secure_key
railway variables set JWT_EXPIRATION_HOURS=24
railway variables set CACHE_TTL=3600
railway variables set MAX_REQUESTS_PER_MINUTE=60
railway variables set ALLOWED_ORIGINS="*"
railway variables set GO_DEBUG=false

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment completed!"
echo "🌐 Your app will be available at the Railway-provided URL"
