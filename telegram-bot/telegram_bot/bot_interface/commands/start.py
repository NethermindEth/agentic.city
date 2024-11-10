from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /start command"""
    if update.message is None or update.effective_user is None:
        return
        
    user = update.effective_user
    await update.message.reply_text(
        f'Hello {user.first_name}! I am your Telegram bot.\n'
        'Use /help to see available commands.'
    )