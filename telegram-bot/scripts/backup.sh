#!/bin/bash

# Exit on error
set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
SOURCE_DIRS=(
    "$PROJECT_ROOT/data"
    "$PROJECT_ROOT/logs"
    "$PROJECT_ROOT/secure"
)
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create the backup
echo "📦 Creating backup..."
tar -czf "$BACKUP_FILE" "${SOURCE_DIRS[@]}" 2>/dev/null || true

# Keep only last 7 days of backups
echo "🧹 Cleaning old backups..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

# Print backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

# Optional: Upload to remote storage
# if command -v aws &> /dev/null; then
#     echo "☁️ Uploading to S3..."
#     aws s3 cp "$BACKUP_FILE" "s3://your-bucket/telegram-bot/backups/"
# fi
