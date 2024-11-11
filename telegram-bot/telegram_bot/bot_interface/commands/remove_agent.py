from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.agents.agent_manager import agent_manager
from typing import Optional

async def find_user_id(username: str, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """Try to get user ID from username"""
    # Currently, there's no direct way to get user ID from username via Bot API
    # We'll need to return None and handle this limitation
    return None

async def remove_agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /remove_agent command"""
    if not update.message or not update.effective_user:
        return

    # Only allow admin to use this command
    admin_id = context.bot_data.get('admin_id', '')
    is_admin = (update.effective_user.username and 
                update.effective_user.username.lower() == admin_id.lower())
    
    if not is_admin:
        await update.message.reply_text("⚠️ This command is only available to the bot administrator.")
        return

    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID.\n"
            "Usage: /remove_agent <user_id>"
        )
        return

    user_identifier = context.args[0]
    
    try:
        # Only accept numeric IDs now
        if user_identifier.isdigit():
            user_id = int(user_identifier)
            if agent_manager.remove_agent(user_id):
                await update.message.reply_text(
                    f"Successfully removed agent for user ID: {user_id}"
                )
            else:
                await update.message.reply_text(
                    f"No agent found for user ID: {user_id}"
                )
        else:
            await update.message.reply_text(
                "Please provide a numeric user ID. Username resolution is not supported."
            )
    except ValueError:
        await update.message.reply_text(
            "Invalid user ID. Please provide a numeric user ID."
        )