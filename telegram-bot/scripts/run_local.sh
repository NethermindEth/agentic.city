#!/bin/bash

# Exit on error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 Setting up environment..."

# Create necessary directories if they don't exist
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/backups"
mkdir -p "$PROJECT_ROOT/monitoring"

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        echo "⚠️  No .env file found. Creating from .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "⚠️  Please edit $PROJECT_ROOT/.env with your configuration"
        exit 1
    else
        echo "❌ No .env or .env.example file found!"
        exit 1
    fi
fi

# Activate poetry environment
echo "🔄 Activating poetry environment..."
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install it first:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
cd "$PROJECT_ROOT"
poetry install

# Start the bot
echo "🤖 Starting bot..."
poetry run python -m telegram_bot.main

# Note: The script will stay running until you press Ctrl+C
# Trap Ctrl+C and cleanup
trap 'echo -e "\n🛑 Stopping bot..."; exit 0' INT
