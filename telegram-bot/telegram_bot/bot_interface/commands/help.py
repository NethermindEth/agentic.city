from telegram import Update
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command"""
    await update.message.reply_text(
        'Available commands:\n'
        '/start - Start the bot\n'
        '/help - Show this help message\n'
        '/status - Check bot status\n'
        '/info - Get information about yourself'
    ) 