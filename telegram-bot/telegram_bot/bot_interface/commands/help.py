"""Module for handling the help command in the Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display available commands and their usage information.

    Args:
        update: The update containing the command
        context: The context for this handler
    """
    if update.message is None:
        return

    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/status - Check bot status\n"
        "/info - Get information about yourself\n"
        "/usage - View token usage statistics\n"
        "/dump - Dump complete agent state\n"
        "/tools - List available tools\n"
        "/tools -v - List tools with detailed information\n"
        "/remove_agent <user_id> - Remove an agent for a specific user"
    )
