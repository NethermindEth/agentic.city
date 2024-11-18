#!/bin/bash

# Exit on error
set -e

echo "🚀 Deploying Telegram Bot..."

# Navigate to project directory
cd "$(dirname "$0")/.."

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p logs backups monitoring

# Install system dependencies if needed
echo "🔧 Installing system dependencies..."
poetry add psutil sentry-sdk prometheus-client

# Setup PM2 if not already installed
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing PM2..."
    npm install -g pm2
fi

# Start/Restart the bot with PM2
echo "🤖 Starting/Restarting bot..."
pm2 describe telegram-bot > /dev/null
if [ $? -eq 0 ]; then
    # Bot exists, restart it
    pm2 restart telegram-bot
else
    # Bot doesn't exist, start it
    pm2 start telegram_bot/main.py --name telegram-bot --interpreter $(which python3)
fi

# Save PM2 configuration
pm2 save

echo "✅ Deployment complete!"
