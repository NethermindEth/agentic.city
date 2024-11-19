"""Module for handling the info command that displays bot and agent information."""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.agents.agent_manager import agent_manager


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display information about the bot and current agent.

    Args:
        update: The update containing the command
        context: The context for this handler
    """
    if (
        update.message is None
        or update.effective_user is None
        or update.effective_chat is None
    ):
        return

    user = update.effective_user
    chat = update.effective_chat

    # Get or create agent for this user
    agent = agent_manager.get_or_create_agent(user.id)
    agent_info = (
        f"\n\n🤖 Agent Info:\n"
        f"Name: {agent.identity.name}\n"
        f"ID: {agent.identity.id}\n"
        f"Model: {agent.model}\n"
        f"Token Usage: {agent.token_usage}"
    )

    info_text = (
        f"👤 User Info:\n"
        f"ID: {user.id}\n"
        f"Name: {user.full_name}\n"
        f'Username: @{user.username if user.username else "None"}\n'
        f"Language: {user.language_code}\n\n"
        f"💭 Chat Info:\n"
        f"Chat ID: {chat.id}\n"
        f"Chat Type: {chat.type}"
        f"{agent_info}"
    )
    await update.message.reply_text(info_text)
