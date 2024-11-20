"""Module for managing agent removal and cleanup operations."""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.agents.agent_manager import agent_manager
from telegram_bot.bot_interface.utils.admin_notify import admin_only


async def find_user_id(
    username: str, context: ContextTypes.DEFAULT_TYPE
) -> Optional[int]:
    """Find a user's ID from their username.

    Args:
        username: The username to look up
        context: The context for this handler

    Returns:
        The user's ID if found, None otherwise
    """
    # Currently, there's no direct way to get user ID from username via Bot API
    # We'll need to return None and handle this limitation
    return None


@admin_only
async def remove_agent_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Remove an agent associated with a specific user ID.

    Args:
        update: The update containing the command
        context: The context for this handler
    """
    message = update.message
    if not message or not context.args:
        if message:
            await message.reply_text(
                "Please provide a user ID.\n" "Usage: /remove_agent <user_id>"
            )
        return

    user_identifier = context.args[0]

    try:
        # Only accept numeric IDs
        if user_identifier.isdigit():
            user_id = int(user_identifier)
            agent_manager.remove_agent(user_id)  # remove_agent now returns None
            await message.reply_text(f"Agent for user {user_id} has been removed.")
        else:
            await message.reply_text(
                "Invalid user ID format. Please provide a numeric ID."
            )
    except Exception as e:
        await message.reply_text(f"Error removing agent: {str(e)}")
