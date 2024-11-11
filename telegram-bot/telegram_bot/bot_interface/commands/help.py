from telegram import Update
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /help command"""
    if update.message is None:
        return
        
    await update.message.reply_text(
        'Available commands:\n'
        '/start - Start the bot\n'
        '/help - Show this help message\n'
        '/status - Check bot status\n'
        '/info - Get information about yourself\n'
        '/usage - View token usage statistics\n'
        '/dump - Dump complete agent state\n'
        '/remove_agent <user_id> - Remove an agent for a specific user'
    ) 