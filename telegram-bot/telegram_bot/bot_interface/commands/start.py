from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    user = update.effective_user
    await update.message.reply_text(
        f'Hello {user.first_name}! I am your Telegram bot.\n'
        'Use /help to see available commands.'
    )