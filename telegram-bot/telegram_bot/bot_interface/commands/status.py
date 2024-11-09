from telegram import Update
from telegram.ext import ContextTypes

# These could be moved to config if they need to be configurable
MESSAGE_RATE_LIMIT = 5
RATE_LIMIT_PERIOD = 60

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status command"""
    await update.message.reply_text(
        'Bot Status:\n'
        '✅ Bot is running\n'
        f'🕒 Current rate limit: {MESSAGE_RATE_LIMIT} messages per {RATE_LIMIT_PERIOD} seconds'
    ) 