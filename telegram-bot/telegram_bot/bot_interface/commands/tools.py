"""Module for managing and displaying available agent tools."""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.agents.agent_manager import agent_manager


async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available tools for the agent.

    Displays a formatted list of tools with their descriptions and usage information.

    Args:
        update: The update containing the command
        context: The context for this handler
    """
    if not update.message or not update.effective_user:
        return

    agent = agent_manager.get_or_create_agent(update.effective_user.id)

    try:
        tools_info = []
        for tool_name, tool in agent.tools.items():
            tool_doc = tool.__doc__ or "No description available"
            tools_info.append(f" {tool_name}:\n{tool_doc}\n")

        if tools_info:
            await update.message.reply_text(
                "Available Tools:\n\n" + "\n".join(tools_info)
            )
        else:
            await update.message.reply_text("No tools available.")
    except Exception:  # Log the error but don't expose details to user
        await update.message.reply_text(
            "Sorry, there was an error retrieving the tools list."
        )
